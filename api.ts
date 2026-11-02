const BASE=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api/v1";
export async function api<T>(path:string):Promise<T>{const r=await fetch(`${BASE}${path}`,{cache:"no-store"});if(!r.ok)throw new Error(await r.text());return r.json()}
export type Player={id:string;full_name:string;primary_position:string;team:string;team_id:string;games_played:number;minutes_per_game:number;net_rtg:number;ts_pct:number;ortg:number;drtg:number;usg_pct:number};
export type Shot={id:string;x:number;y:number;zone_id:string;period:number;clock:number;is_made:boolean;is_clutch:boolean;shot_distance_m:number;shot_type:string;score_margin:number};
