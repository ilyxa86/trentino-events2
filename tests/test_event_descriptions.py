import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from event_descriptions import enrich_descriptions, extract_description, substantive, summarize
from generate_event_summaries import apply_summary


class DescriptionsTest(unittest.TestCase):
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
