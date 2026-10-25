"""Optional X recent search collector. Requires X_BEARER_TOKEN GitHub secret.
This saves attributed public post metadata, not an official trending leaderboard.
"""
import os,json,datetime,urllib.request,urllib.parse
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'docs'/'x_posts.json'
def main():
 token=os.environ.get('X_BEARER_TOKEN','').strip()
 if not token:
  if not OUT.exists():OUT.write_text(json.dumps({'posts':[],'fetched_at':None,'status':'not_configured'},indent=2))
  print('X feed skipped: X_BEARER_TOKEN not provided.');return
 queries=['Nigeria lang:en -is:retweet','(Nigeria OR Nigerian) (economy OR politics OR entertainment OR football) -is:retweet']
 found={}
 for query in queries:
  params=urllib.parse.urlencode({'query':query,'max_results':20,'tweet.fields':'created_at,public_metrics,author_id','expansions':'author_id','user.fields':'username,name'})
  req=urllib.request.Request('https://api.x.com/2/tweets/search/recent?'+params,headers={'Authorization':'Bearer '+token,'User-Agent':'OladayoContentStudio/1.0'})
  try:
   with urllib.request.urlopen(req,timeout=20) as res: result=json.loads(res.read(1_000_000))
   users={u['id']:u for u in result.get('includes',{}).get('users',[])}
   for item in result.get('data',[]):
    u=users.get(item.get('author_id'),{});handle=u.get('username','unknown')
    found[item['id']]={'id':item['id'],'username':handle,'text':item.get('text',''),'created_at':item.get('created_at'),'public_metrics':item.get('public_metrics',{}),'url':f'https://x.com/{handle}/status/{item["id"]}'}
  except Exception as e:print('X search failed:',str(e)[:240]);continue
 if found:OUT.write_text(json.dumps({'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'posts':list(found.values()),'status':'ok'},ensure_ascii=False,indent=2))
 elif not OUT.exists():OUT.write_text(json.dumps({'posts':[],'status':'empty_or_error'},indent=2))
 print('Public X posts:',len(found))
if __name__=='__main__':main()
