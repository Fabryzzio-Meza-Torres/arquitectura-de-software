export type Cand={id:string;text:string;rel:number;lex:number;sem:number;fus:number;llm:number}
export type Q={id:string;query:string;cands:Cand[];rankA:string[];rankB:string[];times:{search_ms:number;fusion_ms:number;llm_ms:number}}
export type IdxItem={id:string;query:string;hit:boolean;A:{[k:string]:number}|null;B:{[k:string]:number}|null;t:Q['times']}
export type Summary={quality:{queries:number;metrics:Record<string,{A:number;B:number;delta:number;CI95:[number,number];wins:number;ties:number;losses:number}>};
 latency:Record<'A'|'B',{p50_ms:number;p95_ms:number;p99_ms:number;throughput_requests_per_s:number;continuity_within_2500_ms:number}>;
 concurrency:{concurrency:number;throughput_requests_per_s:number;p50_ms:number;p99_ms:number;continuity_within_2500_ms:number}[];
 batching:Record<string,{mean_s:number;n:number}>;latSamples:Record<'A'|'B',number[]>}
