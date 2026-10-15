import sys
import unittest
from unittest.mock import patch
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from event_descriptions import enrich_descriptions, extract_description, substantive, summarize, discard_invalid_source_copy, event_detail_url, description_from_record
from generate_event_summaries import apply_summary, response_evidence, evidence_key, request_with_backoff
from enrich_event_links_and_images import best_anchor, concrete_match


class DescriptionsTest(unittest.TestCase):
    def test_short_event_titles_match_exact_heading_but_similar_festivals_do_not(self):
        page = BeautifulSoup('<title>Vai via / Eventi / Agenda Trento</title><h1>Vai via</h1>', 'html.parser')
        self.assertTrue(concrete_match('Vai via', page, 'https://official.example/Eventi/Vai-via'))
        other = BeautifulSoup('<title>Festa della Noce</title><h1>Festa della Noce</h1>', 'html.parser')
        self.assertFalse(concrete_match('Festa del Latte', other, 'https://official.example/events/festa-della-noce'))

    def test_play_synopsis_is_selected_after_shared_series_intro(self):
        page = BeautifulSoup('<h1>Via Pál</h1><article class="it-page-section"><p>A school theatre programme brings art and education together for pupils of all ages.</p><h3>Via Pál</h3><p>Two actors bring Molnár’s novel to the stage, exploring friendship, loyalty and conflict through the boys’ struggle for their playground.</p></article>', 'html.parser')
        self.assertIn('Two actors', extract_description(page))
        self.assertNotIn('school theatre programme', extract_description(page))

    def test_temporary_api_limit_retries_without_losing_the_batch(self):
        class Limited(Exception):
            status_code = 429
            code = 'rate_limit_exceeded'
        class Responses:
            calls = 0
            def create(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise Limited()
                return 'complete'
        class Client:
            responses = Responses()
        with patch('generate_event_summaries.time.sleep') as sleep:
            self.assertEqual(request_with_backoff(Client()), 'complete')
            sleep.assert_called_once()

    def test_image_only_calendar_links_resolve_by_event_slug(self):
        page = BeautifulSoup('<a href="/en/weather/garda-trentino">Garda Trentino</a><a href="/en/events/silk-heritage-walk_123"><img alt=""></a>', 'html.parser')
        self.assertEqual(best_anchor('Silk heritage walk', page, 'https://official.example/events'),
                         'https://official.example/en/events/silk-heritage-walk_123')
        self.assertIsNone(best_anchor('Garda Trentino Xmas Trail', page, 'https://official.example/events'))
    def test_exhausted_credit_is_not_retried(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        error = RuntimeError('credit exhausted')
        error.code = 'credit_balance_exhausted'
        error.status_code = 429
        create = Mock(side_effect=error)
        client = SimpleNamespace(responses=SimpleNamespace(create=create))
        with patch('generate_event_summaries.time.sleep') as sleep:
            with self.assertRaises(RuntimeError):
                request_with_backoff(client)
        self.assertEqual(create.call_count, 1)
        sleep.assert_not_called()

    def test_search_evidence_handles_optional_null_fields(self):
        raw = {'output': [{'content': None, 'action': {'sources': None}},
                          {'content': [{'annotations': None}]},
                          {'action': {'sources': [{'url': 'https://official.example/events/walk'}]}}]}
        self.assertEqual(response_evidence(raw), {'https://official.example/events/walk'})
        self.assertEqual(evidence_key('https://www.official.example/events/walk/?utm_source=search#info'),
                         evidence_key('https://official.example/events/walk'))
        self.assertNotEqual(evidence_key('https://official.example/events?id=1'),
                            evidence_key('https://official.example/events?id=2'))
    def test_enumerator_retains_actual_teaser_but_not_title_and_date(self):
        record = {'sourceId': 'comune_trento_events', 'title': 'Mercatino del Riuso',
                  'rawText': 'Evento Mercatino del Riuso 18 Ottobre 2026 Un’occasione per scambiare libri, vestiti e oggetti senza usare denaro.'}
        self.assertIn('scambiare libri', description_from_record(record)['it'])
        record['rawText'] = 'Evento Mercatino del Riuso 18 Ottobre 2026'
        self.assertEqual(description_from_record(record), {})

    def test_agenda_trento_article_excludes_site_footer(self):
        page = BeautifulSoup('<article class="it-page-section"><p>A swap market gives books, clothing and household objects a second life without using money.</p></article><footer>The city calendar promotes all regional events and activities.</footer>', 'html.parser')
        self.assertIn('swap market', extract_description(page))
        self.assertNotIn('city calendar', extract_description(page))

    def test_weather_and_calendar_are_not_event_evidence(self):
        self.assertFalse(event_detail_url('https://official.example/en/weather/garda-trentino'))
        self.assertFalse(event_detail_url('https://official.example/en/discover/events?page=2'))
        self.assertTrue(event_detail_url('https://official.example/en/discover/events/silk-walk_123'))
        event = {'description': {'en': 'Sunglasses or umbrella? Check out the weather for the next five days.'},
                 'descriptionSources': {'en': 'https://official.example/en/weather/garda-trentino'}}
        self.assertTrue(discard_invalid_source_copy(event))
        self.assertEqual(event['description'], {})

    def test_placeholder_is_not_a_summary(self):
        for text in [
            '“Example” event in Trento. See the official event page for the latest details.',
            'It runs tomorrow. This gives you the key timing and location before opening the full programme.',
            'Veranstaltung in Trento. Aktuelle Details finden Sie auf der offiziellen Veranstaltungsseite.',
        ]:
            self.assertFalse(substantive(text))

    def test_body_copy_excludes_navigation_and_related_events(self):
        soup = BeautifulSoup('''<nav>Book hotels and holidays in Trentino</nav>
          <article class="primary"><div class="desc"><p>A guided walk explores silk mills and the waterways that powered Rovereto's textile industry.</p></div></article>
          <aside>Other events and booking forms should never become a description.</aside>''', 'html.parser')
        result = extract_description(soup)
        self.assertIn('silk mills', result)
        self.assertNotIn('hotels', result)
        self.assertNotIn('booking forms', result)

    def test_structured_data_uses_event_not_organization(self):
        soup = BeautifulSoup('''<script type="application/ld+json">{"@graph":[
          {"@type":"Organization","description":"Tourist information for everyone visiting the region."},
          {"@type":"Event","description":"The exhibition brings Roman mosaics and painted wall fragments together to reveal the colours of ancient Trento."}]}</script>''', 'html.parser')
        self.assertIn('Roman mosaics', extract_description(soup))

    def test_alternate_languages_preserve_curated_translation(self):
        soup = BeautifulSoup('''<html lang="it"><link hreflang="en" href="/en/walk"><link hreflang="de" href="https://other.example/walk"><div class="descrizione"><p>A walk visits the silk mills and explains the history of silk production in Rovereto.</p></div></html>''', 'html.parser')
        curated = "Eine Führung erklärt die Geschichte der Seidenproduktion und besucht ehemalige Spinnereien."
        event = {"description": {"de": curated, "en": "See the official event page for the latest details."}}
        calls = []
        def fetch(url):
            calls.append(url)
            return BeautifulSoup('<html lang="en"><meta name="description" content="Explore the silk mills and waterways on a guided tour of Rovereto’s textile heritage."></html>', 'html.parser'), url, ""
        enrich_descriptions(event, soup, 'https://official.example/it/walk', fetch)
        self.assertEqual(event['description']['de'], curated)
        self.assertIn('waterways', event['description']['en'])
        self.assertEqual(calls, ['https://official.example/en/walk'])
        self.assertEqual(event['descriptionStatus'], 'complete')

    def test_unverified_generated_evidence_is_rejected(self):
        event = {"description": {}}
        result = {lang: 'A guided visit explains the silk industry through surviving mills and historic waterways.' for lang in ('de', 'en', 'it')}
        result['evidenceUrl'] = 'https://invented.example/event'
        self.assertFalse(apply_summary(event, result, {'https://official.example/event'}))
        self.assertEqual(event['description'], {})

    def test_summary_keeps_sentence_boundary_and_strips_markup(self):
        text = '<p>This exhibition displays Roman mosaics and painted fragments from archaeological excavations. Visitors can explore how colour shaped private and public spaces. A third sentence is unnecessary.</p>'
        result = summarize(text)
        self.assertNotIn('<p>', result)
        self.assertNotIn('third', result)
        self.assertTrue(result.endswith('spaces.'))


if __name__ == '__main__':
    unittest.main()
