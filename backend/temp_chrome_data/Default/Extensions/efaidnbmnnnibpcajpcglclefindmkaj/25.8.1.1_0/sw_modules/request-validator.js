/*************************************************************************
* ADOBE CONFIDENTIAL
* ___________________
*
*  Copyright 2015 Adobe Systems Incorporated
*  All Rights Reserved.
*
* NOTICE:  All information contained herein is, and remains
* the property of Adobe Systems Incorporated and its suppliers,
* if any.  The intellectual and technical concepts contained
* herein are proprietary to Adobe Systems Incorporated and its
* suppliers and are protected by all applicable intellectual property laws,
* including trade secret and or copyright laws.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Adobe Systems Incorporated.
**************************************************************************/
import{loggingApi as e}from"../common/loggingApi.js";const s=18e5,t=100,r=new Map,o=(s,o)=>{if(r.size>=t){e.warn({message:"Max pending requests reached",requestId:s,count:r.size});const t=r.keys().next().value;r.delete(t),e.warn({message:"Removed oldest request",requestId:t})}r.set(s,{timestamp:Date.now(),used:!1,source:o})},u=t=>{if(!t)return!1;const o=r.get(t);if(!o)return e.error({message:"Request validation: Unknown request ID",requestId:t}),!1;return Date.now()-o.timestamp>s?(r.delete(t),e.error({message:"Request validation: Request expired",requestId:t,source:o.source}),!1):o.used?(e.error({message:"Request validation: Request ID already used",requestId:t,source:o.source}),!1):(o.used=!0,r.set(t,o),!0)},a=()=>{const e=Date.now();r.forEach((t,o)=>{(e-t.timestamp>s||t.used)&&r.delete(o)})};export{o as registerRequestId,u as isRequestIdValid,a as cleanupUsedOrExpiredRequests};