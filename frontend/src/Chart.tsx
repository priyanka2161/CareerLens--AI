import {useEffect,useRef} from 'react';
import type {Data,Layout} from 'plotly.js';
export default function Chart({data,layout={},label,dark}:{data:Data[];layout?:Partial<Layout>;label:string;dark:boolean}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{let disposed=false;let observer:ResizeObserver|undefined;const el=ref.current;if(!el)return;
 import('plotly.js-dist-min').then(({default:Plotly})=>{if(disposed)return;Plotly.react(el,data,{autosize:true,height:310,margin:{l:55,r:20,t:20,b:55},paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'Inter, system-ui, sans-serif',size:13,color:dark?'#c3cee0':'#54627a'},xaxis:{gridcolor:dark?'#29374d':'#edf0f5'},yaxis:{gridcolor:dark?'#29374d':'#edf0f5'},...layout},{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d'],toImageButtonOptions:{format:'png',filename:'careerlens-demo-chart'}});observer=new ResizeObserver(()=>Plotly.Plots.resize(el));observer.observe(el);}).catch(()=>{if(el)el.textContent='Chart could not load. View the data table below.';});
 return ()=>{disposed=true;observer?.disconnect();import('plotly.js-dist-min').then(({default:Plotly})=>{if(el)Plotly.purge(el);});};
 },[data,layout,dark]);
 return <div ref={ref} className="chart" role="img" aria-label={label}/>;
}
