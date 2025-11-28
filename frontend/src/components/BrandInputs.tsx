import React from "react";
export function BrandInputs(props:{
  value:{primary:string,secondary:string,accent:string},
  onChange:(v:{primary:string,secondary:string,accent:string})=>void
}){
  const v = props.value;
  return (
    <div className="row">
      {(["primary","secondary","accent"] as const).map((key)=>(
        <div key={key}>
          <label>{key} Color</label>
          <div className="color-row">
            <input type="color" value={v[key]} onChange={e=>props.onChange({...v, [key]: e.target.value})}/>
            <input type="text" value={v[key]} onChange={e=>props.onChange({...v, [key]: e.target.value})}/>
          </div>
        </div>
      ))}
    </div>
  );
}
