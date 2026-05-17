import re

with open('templates/saved_item_edit.html') as f:
    saved_html = f.read()

with open('templates/edit.html') as f:
    edit_html = f.read()

# 1. Update tab buttons
tabs_replace = """<div class="tabs" id="draftTabs">
              <button type="button" class="tab-btn active" data-tab="base">Core Info</button>
              <button type="button" class="tab-btn" id="auctionTabBtn" data-tab="auction">Auction Details</button>
              <button type="button" class="tab-btn" data-tab="ebay">eBay Draft</button>
              <button type="button" class="tab-btn" data-tab="etsy">Etsy Draft</button>
              <button type="button" class="tab-btn" data-tab="poshmark">Poshmark Draft</button>
              <button type="button" class="tab-btn" data-tab="vinted">Vinted Draft</button>
            </div>"""

edit_html = re.sub(
    r'<div class="tabs" id="draftTabs">[\s\S]*?</div>',
    tabs_replace,
    edit_html
)

# 2. Extract exactly the Poshmark and Vinted tabs.
# The tabs end when the `<div class="button-row"` starts.
posh_vinted_match = re.search(r'(<!-- TAB: POSHMARK -->[\s\S]*?)(?=\s*<div class="button-row")', saved_html)
if posh_vinted_match:
    posh_vinted_html = posh_vinted_match.group(1)
    
    # 3. Inject into edit.html right after Etsy tab
    # Find the end of the Etsy tab which is right before `<div class="button-row"`
    etsy_end_match = re.search(r'(<!-- TAB: ETSY -->[\s\S]*?)(?=\s*<div class="button-row")', edit_html)
    
    if etsy_end_match:
        edit_html = edit_html.replace(etsy_end_match.group(1), etsy_end_match.group(1) + "\n\n" + posh_vinted_html)
    else:
        print("Could not find end of Etsy tab in edit.html")
else:
    print("Could not find Poshmark/Vinted tabs in saved_item_edit.html")

# 4. We also need to copy the applyAiOption javascript!
js_match = re.search(r'function applyAiOption\(opt\) \{.*?\};\s*', saved_html, re.DOTALL)
if js_match:
    js_to_inject = js_match.group(0)
    # replace in edit.html
    # edit.html doesn't have applyAiOption, it's generated dynamically by `inventory_manager_generator.py` for review_options... 
    # WAIT! review_options.html? No, edit.html has an AI option list!
    pass

with open('templates/edit.html', 'w') as f:
    f.write(edit_html)
print("edit.html patched successfully.")
