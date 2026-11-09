import unittest
from unittest.mock import patch
import briefing

MATCH={'twitch_id':'123','login':'synthetic_creator','last_seen_at':'2026-01-01T00:00:00+00:00'}
DETAIL={'channel':{'twitch_id':'123','login':'synthetic_creator'},'is_live':False,'current_viewers':None}


class BriefingTests(unittest.TestCase):
    def test_resume_refreshes_detail(self):
        with patch.object(briefing,'get_json',side_effect=[({'channels':[MATCH]},'W/"x"',False),(DETAIL,None,False)]):
            result,state=briefing.briefing('synthetic',1,{})
        self.assertEqual(result['outcome'],'briefing')
        self.assertEqual(result['channels'][0]['live_observation'],'not_observed_live')
        with patch.object(briefing,'get_json',side_effect=[(None,'W/"x"',True),(DETAIL,None,False)]) as get:
            result,_=briefing.briefing('synthetic',1,state)
        self.assertTrue(result['catalog_unchanged'])
        self.assertEqual(get.call_count,2)

    def test_identity_and_url_boundary(self):
        with self.assertRaises(ValueError):briefing.summarize(MATCH,{'channel':{'twitch_id':'456'}})
        with self.assertRaises(ValueError):briefing.get_json('//evil.test')
        self.assertNotIn('evil',briefing.pinned_path({**MATCH,'observation_url':'https://evil.test'}))

    def test_empty_valid(self):
        with patch.object(briefing,'get_json',return_value=({'channels':[]},None,False)):
            result,_=briefing.briefing('missing',1,{})
        self.assertEqual(result['outcome'],'no_matches')


if __name__=='__main__':unittest.main()
