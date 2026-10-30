import unittest
from collect_mentions import relevant, merge

class CollectorTests(unittest.TestCase):
    def test_relevance(self):
        self.assertTrue(relevant('Claudia creates slopcore videos'))
        self.assertTrue(relevant('claudia.gallery'))
        self.assertFalse(relevant('Claudia Schiffer at fashion week'))
    def test_unverified_dedup(self):
        data={'verified':[{'url':'https://example.org/verified'}],'candidates':[]}
        new=[{'url':'https://example.org/verified'},{'url':'https://example.org/new','date':'2026-10-30','verification':'Verified','tier':'Major'}]
        r=merge(data,new,'now')
        self.assertEqual(len(r['candidates']),1)
        self.assertEqual(r['candidates'][0]['verification'],'Needs review')
        self.assertEqual(r['candidates'][0]['tier'],'Unclassified')

if __name__=='__main__':unittest.main()
