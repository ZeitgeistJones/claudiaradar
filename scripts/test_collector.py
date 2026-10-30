import os
import unittest
from unittest import mock

from collect_mentions import merge, relevant, youtube, reddit, podcast_index, newsdata, apify_web_search


class CollectorTests(unittest.TestCase):
    def test_relevance_strong_and_soft(self):
        self.assertTrue(relevant('Claudia creates slopcore videos'))
        self.assertTrue(relevant('claudia.gallery'))
        self.assertTrue(relevant('Watch claudia_popstar'))
        self.assertTrue(relevant('AI popstar Claudia profile'))
        self.assertFalse(relevant('Claudia Schiffer at fashion week'))
        self.assertFalse(relevant('Someone named Claudia bought coffee'))

    def test_unverified_dedup(self):
        data = {
            'verified': [{'url': 'https://example.org/verified'}],
            'candidates': [],
        }
        new = [
            {'url': 'https://example.org/verified'},
            {
                'url': 'https://example.org/new',
                'date': '2026-10-30',
                'verification': 'Verified',
                'tier': 'Major',
            },
        ]
        result = merge(data, new, 'now')
        self.assertEqual(len(result['candidates']), 1)
        self.assertEqual(result['candidates'][0]['verification'], 'Needs review')
        self.assertEqual(result['candidates'][0]['tier'], 'Unclassified')
        self.assertEqual(result['updatedAt'], 'now')

    def test_keyed_sources_skip_without_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'skipped: no YOUTUBE_API_KEY'):
                youtube()
            with self.assertRaisesRegex(RuntimeError, 'skipped: no REDDIT_CLIENT_ID'):
                reddit()
            with self.assertRaisesRegex(RuntimeError, 'skipped: no PODCASTINDEX_KEY'):
                podcast_index()
            with self.assertRaisesRegex(RuntimeError, 'skipped: no NEWSDATA_API_KEY'):
                newsdata()
            with self.assertRaisesRegex(RuntimeError, 'skipped: no APIFY_TOKEN'):
                apify_web_search()


if __name__ == '__main__':
    unittest.main()
