import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from merge_summary_updates import merge_summaries


class MergeTest(unittest.TestCase):
    def test_concurrent_data_and_curated_text_are_preserved(self):
        base = [{'id': 'walk', 'name': {'it': 'Walk'}, 'startDate': '2026-10-20',
                 'endDate': '2026-10-20', 'venue': 'Old venue', 'description': {}}]
        generated = copy.deepcopy(base)
        generated[0]['description'] = {'de': 'Eine Führung erklärt die Geschichte der Textilindustrie anhand historischer Spinnereien.',
                                       'en': 'A guided walk explains the textile industry through its surviving historic silk mills.'}
        latest = copy.deepcopy(base)
        latest[0]['venue'] = 'Corrected venue'
        curated = 'A curator-led visit explores the historical silk industry and the people who worked in its mills.'
        latest[0]['description'] = {'en': curated}
        merged = merge_summaries(base, generated, latest)[0]
        self.assertEqual(merged['venue'], 'Corrected venue')
        self.assertEqual(merged['description']['en'], curated)
        self.assertIn('Textilindustrie', merged['description']['de'])

    def test_rescheduled_event_requires_new_research(self):
        base = [{'id': 'festival', 'startDate': '2026-10-20', 'description': {}}]
        generated = copy.deepcopy(base)
        generated[0]['description'] = {'en': 'A festival brings together musicians and artists for live performances in the town square.'}
        latest = copy.deepcopy(base)
        latest[0]['startDate'] = '2027-10-20'
        self.assertEqual(merge_summaries(base, generated, latest)[0]['description'], {})


if __name__ == '__main__':
    unittest.main()
