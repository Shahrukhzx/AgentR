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
!function(){function e(e,t){const n=function(e){if(!e)return null;const t=e.match(/filename=([^;]+)/i);if(t){let e=t[1].trim();e=e.replace(/^["']|["']$/g,""),e=e.replace(/\\(.)/g,"$1");try{const t=decodeURIComponent(e);t===e||t.includes("�")||(e=t)}catch(e){}return e}return null}(e.headers.get("Content-Disposition"));document.dispatchEvent(new CustomEvent(t,{detail:{responseUrl:e.url,success:!0,filename:n}}))}!function(){const t=window.fetch;window.fetch=function(...n){const o=n[0]||"";if(o&&(o.includes("service.svc?action=GetAttachmentDownloadToken")||o.includes("service.svc/s/GetFileAttachment"))){const c=o.includes("service.svc?action=GetAttachmentDownloadToken")?"acrobat-outlook-token-intercept-response":"acrobat-outlook-attachment-intercept-response";return t(...n).then(t=>(t.ok?(async()=>{if("acrobat-outlook-token-intercept-response"===c){const e=t.clone(),n=await e.json();if(e.url)try{const t=new URL(e.url);!t||"outlook.live.com"!==t?.hostname&&"outlook.office.com"!==t?.hostname&&"outlook.office365.com"!==t?.hostname||document.dispatchEvent(new CustomEvent(c,{detail:{success:!0,data:n,responseUrl:e.url}}))}catch(e){document.dispatchEvent(new CustomEvent(c,{detail:{success:!1,error:e.message}}))}}else e(t,c)})():(async()=>{document.dispatchEvent(new CustomEvent(c,{detail:{success:!1,status:t.status}}))})(),t)).catch(e=>{throw document.dispatchEvent(new CustomEvent(c,{detail:{success:!1,error:e.message}})),e})}return t(...n)}}()}();