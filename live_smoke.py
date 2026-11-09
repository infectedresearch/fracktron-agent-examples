"""Explicit real-network smoke; no credentials, writes, or telemetry uploads."""
import briefing

first,state=briefing.briefing('nerdragefred',1,{})
assert first['outcome']=='briefing', 'Sample channel unavailable; inspect before declaring service failure'
assert first['channels'][0]['twitch_id'].isdigit()
second,_=briefing.briefing('nerdragefred',1,state)
assert second['catalog_unchanged'], 'Observation changed between reads; rerun to confirm'
assert second['detail_refetched']
print('PASS: public discovery → numeric identity → evidence briefing → conditional catalog resume')
