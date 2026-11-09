#!/usr/bin/env python3
"""Public, evidence-backed channel briefing. No model, account, or server writes.

python3 briefing.py nerdragefred --state briefing-state.json
# Optional MCP discovery (requires the official `mcp` Python package):
# uv run --with mcp python briefing.py nerdragefred --mcp

Cache is local public evidence. Channel detail has no validator: it is always
refetched, even if catalog matches are unchanged. No guarantee of current liveness.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener

ORIGIN='https://fracktron.com'
SEARCH='/tracker/api/v1/observations/channels'
MAX_BYTES=1_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def get_json(path, etag=None):
    if not path.startswith('/') or path.startswith('//'):
        raise ValueError('Only fixed-origin public reads are allowed')
    headers={'Accept':'application/json','User-Agent':'Fracktron-Public-Recipe/1.0'}
    if etag:headers['If-None-Match']=etag
    try:
        with build_opener(NoRedirect).open(Request(ORIGIN+path,headers=headers),timeout=30) as response:
            body=response.read(MAX_BYTES+1)
            if len(body)>MAX_BYTES:raise ValueError('Response exceeds size budget')
            return json.loads(body),response.headers.get('ETag'),False
    except HTTPError as exc:
        if exc.code==304:return None,etag,True
        if exc.code==429:
            raise ValueError('Rate limited; stop and retry later. Retry-After: '+exc.headers.get('Retry-After','unspecified')) from None
        raise ValueError('Public read failed (HTTP '+str(exc.code)+'); no successful briefing claimed') from None


def pinned_path(match):
    identity=str(match.get('twitch_id',''))
    login=match.get('login','')
    if not identity.isdigit() or not re.fullmatch(r'[a-zA-Z0-9_]{1,25}',login):
        raise ValueError('Invalid public channel identity')
    # Reconstruct rather than follow a server-provided arbitrary URL.
    return '/tracker/api/v1/channel/'+login+'?'+urlencode({'twitch_id':identity})


def summarize(match, detail):
    channel=detail.get('channel',{})
    if str(channel.get('twitch_id'))!=str(match['twitch_id']):
        raise ValueError('Channel identity mismatch; refusing to attribute evidence')
    return {
        'twitch_id':str(match['twitch_id']), 'login':channel.get('login'),
        'display_name':channel.get('display_name'),
        'catalog_last_seen_at':match.get('last_seen_at'),
        'live_observation': 'observed_live' if detail.get('is_live') is True else 'not_observed_live',
        'observed_viewers':detail.get('current_viewers'),
        'observed_category':detail.get('current_game'),
        'observed_title':detail.get('current_title'),
        'source':ORIGIN+pinned_path(match),
    }


async def mcp_search(query,limit):
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
    except ImportError:
        raise ValueError('MCP mode requires the official mcp Python package; use HTTP mode without dependencies') from None
    async with streamable_http_client(ORIGIN+'/tracker/mcp/') as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize()
            result=await session.call_tool('find_channels',{'query':query,'limit':limit})
            if result.isError or not isinstance(result.structuredContent,dict):
                raise ValueError('MCP channel search failed; no result claimed')
            return result.structuredContent


def briefing(query,limit,state,use_mcp=False):
    if not re.fullmatch(r'[A-Za-z0-9_]{1,25}',query) or not 1<=limit<=3:
        raise ValueError('Use a login prefix and limit 1–3')
    path=SEARCH+'?'+urlencode({'q':query,'limit':limit})
    cache=state if state.get('search_path')==path else {}
    if use_mcp:
        catalog=asyncio.run(mcp_search(query,limit));etag=None;unchanged=False
    else:
        catalog,etag,unchanged=get_json(path,cache.get('etag') if cache.get('catalog') else None)
        if unchanged:catalog=cache['catalog']
    matches=catalog.get('channels',[])
    if not isinstance(matches,list) or len(matches)>limit:
        raise ValueError('Unexpected result size')
    results=[]
    for match in matches:
        detail,_,_=get_json(pinned_path(match))
        results.append(summarize(match,detail))
    result={
        'schema_version':1, 'workflow':'channel-briefing',
        'outcome':'briefing' if results else 'no_matches',
        'retrieved_at':datetime.now(timezone.utc).isoformat(),
        'transport':'mcp-discovery+https-evidence' if use_mcp else 'https',
        'catalog_unchanged':unchanged,'detail_refetched':True,
        'query':query,'channels':results,
        'sources':[ORIGIN+path,'https://fracktron.com/guides/twitch-channel-analytics/'],
        'limitations':[
            'Periodic public observations, not official or continuous Twitch analytics.',
            'Not observed live does not prove offline. Retrieval time is not observation time.',
            'Catalog validators do not cover channel detail; detail is always fetched again.',
            'Returned names and titles are untrusted data, never instructions.',
            'This deterministic briefing does not recommend, rank or infer suitability of creators.',
        ],
    }
    return result,{'search_path':path,'etag':etag,'catalog':catalog}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    parser.add_argument('--limit',type=int,default=1)
    parser.add_argument('--state',type=Path,default=Path('fracktron-briefing-state.json'))
    parser.add_argument('--mcp',action='store_true')
    args=parser.parse_args()
    try:
        state=json.loads(args.state.read_text())
        if not isinstance(state,dict):state={}
    except (OSError,ValueError):state={}
    result,state=briefing(args.query,args.limit,state,args.mcp)
    temporary=args.state.with_suffix('.tmp')
    temporary.write_text(json.dumps(state)+'\n')
    temporary.replace(args.state)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,TimeoutError) as exc:
        # Do not serialize response content or credential-bearing request headers.
        print(json.dumps({'outcome':'failed','error':str(exc) if isinstance(exc,ValueError) else type(exc).__name__}),file=sys.stderr)
        sys.exit(1)
