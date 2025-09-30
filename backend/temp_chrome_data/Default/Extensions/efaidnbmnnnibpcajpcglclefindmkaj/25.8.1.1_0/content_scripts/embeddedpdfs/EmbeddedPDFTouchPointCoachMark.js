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
const FTE_STATE_STORAGE_KEY="embeddedPDFTouchPointFTEState";class EmbeddedPDFTouchPointCoachMark{shouldResetFteToolTip(t,e){return-1!==t?.resetDay&&e>t?.resetDay}async initFteStateAndConfig(t){const e=(new Date).getTime();let o={count:0,nextDate:e};o=(await chrome.storage.local.get(FTE_STATE_STORAGE_KEY))?.[FTE_STATE_STORAGE_KEY]||o;const i=t?.touchPointConfig?.tooltip;return this?.shouldResetFteToolTip(i,e)&&(o.count=0,o.nextDate=e),chrome.storage.local.set({[FTE_STATE_STORAGE_KEY]:o}),o}constructor(){import(chrome.runtime.getURL("content_scripts/gsuite/fte-utils.js")).then(t=>this.fteUtils=t)}id="embeddedpdfscoachmark";timeout=3e3;async render(){const t=await chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-config"});t?.enableEmbeddedPDFTouchPoint&&chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-fte",frameId:this.frameId})}isTouchPointPresent(){return embeddedPDFTouchPointAddedPromise}isTouchPointPositionAllowsForFTE(t){return t?.top>=0&&t?.left>=0&&t?.bottom+50<=window.innerHeight&&t?.right<=window.innerWidth}async isEligible(){let t;const e=await chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-config"});if(!e?.enableEmbeddedPDFTouchPoint)return Promise.resolve(!1);let o=new Promise(e=>{t=e});const i=await this.initFteStateAndConfig(e),{isTouchPointPresent:n,frameId:s,position:d}=await this.isTouchPointPresent();if(this.frameId=s,n&&this.isTouchPointPositionAllowsForFTE(d)){const o=e?.touchPointConfig?.tooltip,n=await(this.fteUtils?.shouldShowFteTooltip(o,i,!!o));t(n)}return o}}