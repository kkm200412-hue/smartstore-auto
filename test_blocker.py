import streamlit as st
import streamlit.components.v1 as components

st.write('Test page')

html_code = """
<script>
try {
    const parentDoc = window.parent.document;
    
    // Make sure we only attach the listener once
    if (!parentDoc.getElementById('shortcut-blocker-installed')) {
        const marker = parentDoc.createElement('div');
        marker.id = 'shortcut-blocker-installed';
        marker.style.display = 'none';
        parentDoc.body.appendChild(marker);
        
        parentDoc.addEventListener('keydown', function(e) {
            if (e.key === 'c' || e.key === 'C') {
                const target = e.target;
                const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
                if (!isInput) {
                    e.stopPropagation();
                    e.preventDefault();
                }
            }
        }, { capture: true });
        console.log('Shortcut blocker installed');
    }
} catch (err) {
    console.log('Error installing shortcut blocker:', err);
}
</script>
"""
components.html(html_code, height=0, width=0)
