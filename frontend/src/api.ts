const BASE=import.meta.env.VITE_API_BASE || '/api';
let sessionPromise:Promise<string>|null=null;
export async function session():Promise<string>{
 const existing=localStorage.getItem('careerlens-session');if(existing)return existing;
 if(!sessionPromise)sessionPromise=fetch(BASE+'/session',{method:'POST'}).then(async r=>{if(!r.ok)throw Error('Could not start a session. Check that the backend is running.');const data=await r.json();localStorage.setItem('careerlens-session',data.token);return data.token as string;}).finally(()=>{sessionPromise=null;});
 return sessionPromise;
}
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const token=await session();const headers=new Headers(options.headers);headers.set('Authorization',`Bearer ${token}`);if(options.body && !(options.body instanceof FormData))headers.set('Content-Type','application/json');
 const response=await fetch(BASE+path,{...options,headers});
 if(!response.ok){let msg='Request failed. Please try again.';try{const e=await response.json();msg=typeof e.detail==='string'?e.detail:JSON.stringify(e.detail);}catch{/* preserve readable default */}if(response.status===401){localStorage.removeItem('careerlens-session');msg+=' Refresh to create a new session.';}throw Error(msg);}
 return response.status===204?undefined as T:response.json();
}
