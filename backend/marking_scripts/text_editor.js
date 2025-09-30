function detectTextEditor() {
    function getXPath(element) {
        if (!element) return null;
        if (element.id) return `//*[@id="${element.id}"]`;
        let path = [];
        for (; element && element.nodeType === Node.ELEMENT_NODE; element = element.parentNode) {
            let index = 1;
            for (let sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
                if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === element.tagName) {
                    index++;
                }
            }
            let tagName = element.tagName.toLowerCase();
            path.unshift(index > 1 ? `${tagName}[${index}]` : tagName);
        }
        return path.length ? `/${path.join('/')}` : null;
    }

    function getEditorElement() {
        // Check if the user is actively focused inside an editor
        if (document.activeElement && document.activeElement.isContentEditable) {
            return document.activeElement;
        }
        // Otherwise, find the first editable element
        return document.querySelector('[contenteditable="true"]') || document.querySelector('textarea');
    }

    const editor = getEditorElement();
    if (editor) {
        const rect = editor.getBoundingClientRect();
        return {
            detected: true,
            XPath: getXPath(editor),
            X: Math.round(rect.left + window.scrollX + rect.width / 2),
            Y: Math.round(rect.top + window.scrollY + rect.height / 2)
        };
    }
    return { detected: false };
}
