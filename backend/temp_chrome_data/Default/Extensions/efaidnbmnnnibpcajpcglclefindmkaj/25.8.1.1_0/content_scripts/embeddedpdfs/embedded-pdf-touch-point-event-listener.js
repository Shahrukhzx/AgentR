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
const sendAnalyticsForEmbeddedPDFLoad=(e,d)=>{try{const o=new URL(window.location.href).hostname;d={...d,domain:o},chrome.runtime.sendMessage({main_op:"analytics",analytics:[[e,d]]})}catch(e){}};let embeddedPDFTouchPointAddedPromiseResolve,isEmbeddedPDFTouchPointAdded=!1;function isEmbeddedPDFTouchPointRendered(){return isEmbeddedPDFTouchPointAdded}const start=performance.now(),embeddedPDFTouchPointAddedPromise=new Promise(e=>{embeddedPDFTouchPointAddedPromiseResolve=e});chrome.runtime.onMessage.addListener(e=>{if("added-embedded-pdf-touch-point"===e?.type){embeddedPDFTouchPointAddedPromiseResolve({isTouchPointPresent:!0,frameId:e.frameId,position:e.position}),isEmbeddedPDFTouchPointAdded=!0;const d=performance.now()-start;sendAnalyticsForEmbeddedPDFLoad(d<500?"DCBrowserExt:EmbeddedPDF:LoadTime:Fast":d<1500?"DCBrowserExt:EmbeddedPDF:LoadTime:Normal":"DCBrowserExt:EmbeddedPDF:LoadTime:Slow")}});