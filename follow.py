#!/usr/bin/env python3
"""Follow platform observation changes; standard library only, no credentials.

python3 follow.py --checks 2 --interval 60
Persisted cursor contains only a public HTTP validator. Check intervals >=60s.
304 means semantically unchanged, not a fresh observation or proof of liveness.
"""
import argparse
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

URL='https://fracktron.com/tracker/api/v1/observations/platform'


def poll(etag=None):
    headers={'Accept':'application/json','User-Agent':'Fracktron-Public-Recipe/1.0'}
    if etag:headers['If-None-Match']=etag
    try:
        with urlopen(Request(URL,headers=headers),timeout=30) as response:
            data=json.loads(response.read(100_000))
            return {'changed':True,'etag':response.headers.get('ETag'),'observation':data}
    except HTTPError as exc:
        if exc.code==304:
            return {'changed':False,'etag':etag}
        if exc.code==429:
            raise SystemExit('Rate limited. Stop; retry after '+exc.headers.get('Retry-After','the server limit window')+' seconds.') from None
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checks',type=int,default=2)
    parser.add_argument('--interval',type=int,default=60)
    parser.add_argument('--cursor',type=Path,default=Path('fracktron-observation-cursor.json'))
    args=parser.parse_args()
    if not 1<=args.checks<=1440 or args.interval<60:
        parser.error('Use 1–1440 checks and interval >=60 seconds')
    try:
        etag=json.loads(args.cursor.read_text()).get('etag')
    except (OSError,ValueError):
        etag=None
    for i in range(args.checks):
        result=poll(etag)
        print(json.dumps(result),flush=True)
        etag=result['etag']
        if etag:
            temporary=args.cursor.with_suffix('.tmp')
            temporary.write_text(json.dumps({'etag':etag})+'\n')
            temporary.replace(args.cursor)
        if i+1<args.checks:time.sleep(args.interval)


if __name__=='__main__':
    main()
