-- ankdown.lua: Extract Anki cards from Markdown lists with Media support

local json = require 'pandoc.json'
local cards = {}
local media = {}
local deck_meta = {title = "Ankdown Deck", model = "Ankdown Model", tags = {}}

-- Helper to convert blocks to HTML
function blocks_to_html(blocks)
    if not blocks or #blocks == 0 then return "" end
    local html = pandoc.write(pandoc.Pandoc(blocks), 'html'):gsub("\n", " "):gsub("^%s*(.-)%s*$", "%1")
    return html
end

-- Helper to render TikZ/TikZ-CD to SVG
local function render_tikz(content)
    local hash = pandoc.utils.sha1(content)
    local svg_filename = "tikz-" .. hash .. ".svg"
    local svg_path = "ankdown_media/" .. svg_filename
    
    -- Cache check: if SVG exists, skip compilation
    local f = io.open(svg_path, "r")
    if f then
        f:close()
        return svg_filename, svg_path
    end
    
    -- Ensure output directory exists
    os.execute("mkdir -p ankdown_media")
    
    local tmp_base = "tmp-" .. hash
    local tex_filename = tmp_base .. ".tex"
    local tex_file = io.open(tex_filename, "w")
    tex_file:write("\\documentclass[tikz,border=2pt]{standalone}\n")
    tex_file:write("\\usepackage{tikz-cd}\n")
    tex_file:write("\\begin{document}\n")
    tex_file:write(content .. "\n")
    tex_file:write("\\end{document}\n")
    tex_file:close()
    
    -- Compile to SVG via PDF
    os.execute("pdflatex -interaction=nonstopmode " .. tex_filename .. " > /dev/null 2>&1")
    os.execute("pdf2svg " .. tmp_base .. ".pdf " .. svg_path .. " > /dev/null 2>&1")
    
    -- Cleanup temp files
    os.execute("rm -f " .. tmp_base .. ".*")
    
    return svg_filename, svg_path
end

-- Image extraction and TikZ rendering filter
local media_filter = {
    Image = function(img)
        local path = img.src
        -- Skip remote URLs
        if path:match("^http") or path:match("^https") then
            return img
        end
        
        -- Resolve relative path
        local input_file = PANDOC_STATE.input_files[1]
        local abs_path = path
        if input_file then
            local dir = input_file:match("(.*[/\\])") or ""
            abs_path = dir .. path
        end
        
        -- Mangle path for Anki (replace / and \ with %)
        local mangled = path:gsub("[/\\ ]", "%%")
        img.src = mangled
        
        -- Record mapping for CLI (absolute_path:mangled_name)
        table.insert(media, abs_path .. ":" .. mangled)
        
        return img
    end,
    Math = function(m)
        if m.mathtype == 'DisplayMath' then
            return pandoc.RawInline('html', '\\[' .. m.text .. '\\]')
        else
            return pandoc.RawInline('html', '\\(' .. m.text .. '\\)')
        end
    end,
    RawBlock = function(rb)
        if rb.format == 'latex' or rb.format == 'tex' then
            -- Handle TikZ and TikZ-CD by rendering to SVG
            if rb.text:match("\\begin{tikz.-}") then
                local svg_name, svg_abs_path = render_tikz(rb.text)
                local full_abs_path = os.getenv("PWD") .. "/" .. svg_abs_path
                -- Add to media list for CLI bundling
                table.insert(media, full_abs_path .. ":" .. svg_name)
                return pandoc.Para({pandoc.Image({pandoc.Str("Diagram")}, svg_name)})
            else
                return pandoc.RawBlock('html', '\\[' .. rb.text .. '\\]')
            end
        end
    end,
    RawInline = function(ri)
        if ri.format == 'latex' or ri.format == 'tex' then
            return pandoc.RawInline('html', '\\(' .. ri.text .. '\\)')
        end
    end
}

-- If plain text is a per-card tag line ("tags: a, b, c"), return {a,b,c}, else nil.
function parse_card_tags(plain)
    local rest = plain:match('^%s*[Tt][Aa][Gg][Ss]:%s*(.+)$')
    if not rest then return nil end
    local out = {}
    for tag in rest:gmatch('[^,]+') do
        tag = tag:gsub('^%s*(.-)%s*$', '%1')
        if tag ~= '' then table.insert(out, tag) end
    end
    return out
end

function process_list(list)
    for _, item_blocks in ipairs(list.content) do
        -- Apply filters (Math and Images)
        local processed_blocks = pandoc.walk_block(pandoc.Div(item_blocks), media_filter).content

        if #processed_blocks >= 1 then
            local front = blocks_to_html({processed_blocks[1]})
            local back_parts = {}
            local card_tags = {}

            for i = 2, #processed_blocks do
                local block = processed_blocks[i]
                if block.t == 'BulletList' or block.t == 'OrderedList' then
                    for _, subitem in ipairs(block.content) do
                        local tags = parse_card_tags(pandoc.utils.stringify(pandoc.Div(subitem)))
                        if tags then
                            for _, tg in ipairs(tags) do table.insert(card_tags, tg) end
                        else
                            table.insert(back_parts, blocks_to_html(subitem))
                        end
                    end
                else
                    local tags = parse_card_tags(pandoc.utils.stringify(block))
                    if tags then
                        for _, tg in ipairs(tags) do table.insert(card_tags, tg) end
                    else
                        table.insert(back_parts, blocks_to_html({block}))
                    end
                end
            end

            table.insert(cards, {
                front = front,
                back = table.concat(back_parts, "<br>"),
                tags = card_tags
            })
        end
    end
end

-- Metadata extraction
function Meta(meta)
    if meta.title then deck_meta.title = pandoc.utils.stringify(meta.title) end
    if meta.model then deck_meta.model = pandoc.utils.stringify(meta.model) end
    if meta.tags then
        for _, tag in ipairs(meta.tags) do
            table.insert(deck_meta.tags, pandoc.utils.stringify(tag))
        end
    end
end

-- Final output
function Pandoc(doc)
    for _, block in ipairs(doc.blocks) do
        if block.t == 'BulletList' or block.t == 'OrderedList' then
            process_list(block)
        end
    end
    
    local final_cards = {}
    for _, card in ipairs(cards) do
        local c = {front = card.front, back = card.back}
        -- Only include tags if they are not empty to avoid JSON {} vs [] ambiguity
        if #card.tags > 0 then c.tags = card.tags end
        table.insert(final_cards, c)
    end
    
    local output = {
        meta = {
            title = deck_meta.title,
            model = deck_meta.model
        },
        cards = final_cards
    }
    if #deck_meta.tags > 0 then output.meta.tags = deck_meta.tags end
    if #media > 0 then output.media = media end
    
    io.stdout:write(json.encode(output))
    os.exit(0)
end
