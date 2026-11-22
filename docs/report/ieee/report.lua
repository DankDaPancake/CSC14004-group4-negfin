-- Pandoc Lua filter: docs/report/chapterN.md -> phần thân LaTeX cho main.tex (IEEEtran).
-- Gọi qua build.py với -M chapter=N -M refmap="1=negfin,2=spmf".
-- Markdown vẫn là bản gốc; mọi đánh số mục/bảng/công thức/tài liệu do LaTeX sinh lại.

local stringify = pandoc.utils.stringify

local chapter = "0"
local refmap = {}   -- "1" -> khóa BibTeX
local tables = {}   -- số La Mã trong chương -> nhãn LaTeX

local MATH = {
  ["⇒"] = "\\Rightarrow", ["→"] = "\\rightarrow", ["∞"] = "\\infty", ["∪"] = "\\cup",
  ["⊆"] = "\\subseteq", ["∈"] = "\\in", ["≤"] = "\\le", ["≥"] = "\\ge", ["≠"] = "\\neq",
  ["¬"] = "\\neg", ["⌈"] = "\\lceil", ["⌉"] = "\\rceil", ["≈"] = "\\approx", ["↔"] = "\\leftrightarrow",
}

local HEADING_PREFIXES = {
  "^Chương%s+%d+%.%s*", "^[IVX]+%.%s+", "^%d+%.%d+%.%s*", "^%d+%.%s+", "^[A-Z]%.%s+", "^%d+%)%s+",
}

local function latex(blocks)
  return (pandoc.write(pandoc.Pandoc(blocks), "latex"):gsub("%s+$", ""))
end

local function latex_inlines(inlines)
  return latex({ pandoc.Plain(inlines) })
end

local function is_local(target)
  return not target:match("^%a+://") and not target:match("^mailto:")
end

-- "Bảng III." trong Strong đầu đoạn, theo sau là một bảng
local function caption_roman(block)
  if block.t ~= "Para" or #block.content == 0 or block.content[1].t ~= "Strong" then return nil end
  return stringify(block.content[1]):match("^Bảng%s+([IVX]+)%.")
end

-- Tách một Str thành Str/RawInline cho [n] (trích dẫn) và ký hiệu toán Unicode.
local function split_str(text)
  local out, buf = pandoc.List(), ""
  local i = 1
  while i <= #text do
    local num, stop = text:match("^%[(%d+)%]()", i)
    if num and refmap[num] then
      if buf ~= "" then out:insert(pandoc.Str(buf)); buf = "" end
      out:insert(pandoc.RawInline("latex", "\\cite{" .. refmap[num] .. "}"))
      i = stop
    else
      local ch = text:match("^[\0-\127\194-\244][\128-\191]*", i)
      if MATH[ch] then
        if buf ~= "" then out:insert(pandoc.Str(buf)); buf = "" end
        out:insert(pandoc.RawInline("latex", "$" .. MATH[ch] .. "$"))
      else
        buf = buf .. ch
      end
      i = i + #ch
    end
  end
  if buf ~= "" then out:insert(pandoc.Str(buf)) end
  return out
end

local function roman_ref(el)
  if el and el.t == "Str" then
    local r, punct = el.text:match("^([IVX]+)(%p*)$")
    if r and tables[r] then return r, punct end
  end
end

local function fix_inlines(inlines)
  local out = pandoc.List()
  local i = 1
  local last_table = false
  while i <= #inlines do
    local el, nxt, val = inlines[i], inlines[i + 1], inlines[i + 2]
    if el.t == "Str" and el.text == "Bảng" and nxt and nxt.t == "Space" and roman_ref(val) then
      local r, punct = roman_ref(val)
      out:insert(pandoc.RawInline("latex", "Bảng~\\ref{" .. tables[r] .. "}" .. punct))
      last_table = true
      i = i + 3
    elseif last_table and el.t == "Str" and el.text == "và" and nxt and nxt.t == "Space" and roman_ref(val) then
      local r, punct = roman_ref(val)
      out:insert(pandoc.Str("và")); out:insert(pandoc.Space())
      out:insert(pandoc.RawInline("latex", "\\ref{" .. tables[r] .. "}" .. punct))
      i = i + 3
    elseif el.t == "Str" and el.text == "Chương" and nxt and nxt.t == "Space" and val and val.t == "Str"
        and val.text:match("^%d+%p*$") then
      local n, punct = val.text:match("^(%d+)(%p*)$")
      out:insert(pandoc.RawInline("latex", "Mục~\\ref{sec:ch" .. n .. "}" .. punct))
      last_table = false
      i = i + 3
    elseif el.t == "Str" then
      out:extend(split_str(el.text))
      if el.text ~= "và" then last_table = false end
      i = i + 1
    elseif el.t == "Link" and is_local(el.target) then
      local prev = out[#out - 1]
      if i == #inlines and #out >= 2 and out[#out].t == "Space" and prev.t == "Str" and prev.text:match("%.$") then
        out:remove()   -- liên kết "xem thêm" đứng riêng cuối đoạn: bỏ khỏi bản PDF
      else
        out:extend(fix_inlines(el.content))   -- liên kết tới file trong repo: chỉ giữ chữ
      end
      i = i + 1
    else
      if el.t ~= "Space" then last_table = false end
      out:insert(el)
      i = i + 1
    end
  end
  return out
end

local function strip_heading(text)
  for _, pat in ipairs(HEADING_PREFIXES) do
    local stripped = text:gsub(pat, "", 1)
    if stripped ~= text then return stripped end
  end
  return text
end

local function render_table(tbl, roman, caption)
  local ncols = #tbl.colspecs
  local rows = pandoc.List()
  for _, r in ipairs(tbl.head.rows) do rows:insert({ row = r, head = true }) end
  for _, body in ipairs(tbl.bodies) do
    for _, r in ipairs(body.body) do rows:insert({ row = r, head = false }) end
  end

  local maxlen, colmax = 0, {}
  for c = 1, ncols do colmax[c] = 0 end
  for _, item in ipairs(rows) do
    local total = 0
    for c, cell in ipairs(item.row.cells) do
      local len = utf8.len(stringify(cell.contents)) or 0
      total = total + len
      colmax[c] = math.max(colmax[c], len)
    end
    maxlen = math.max(maxlen, total)
  end

  local wide = ncols >= 6 or maxlen > 60
  local width = wide and "\\textwidth" or "\\columnwidth"
  local limit = wide and 120 or 48

  -- cột chữ dài nhất (căn trái) co giãn bằng X khi bảng quá rộng
  local xcol, best = nil, 0
  for c, spec in ipairs(tbl.colspecs) do
    local align = spec[1]
    if (align == "AlignLeft" or align == "AlignDefault") and colmax[c] > best then xcol, best = c, colmax[c] end
  end
  local use_x = maxlen > limit and xcol ~= nil

  local spec = {}
  for c, s in ipairs(tbl.colspecs) do
    local a = s[1]
    if use_x and c == xcol then spec[c] = "X"
    elseif a == "AlignRight" then spec[c] = "r"
    elseif a == "AlignCenter" then spec[c] = "c"
    else spec[c] = "l" end
  end

  local lines = {}
  for _, item in ipairs(rows) do
    local cells = {}
    for c, cell in ipairs(item.row.cells) do
      local s = latex(cell.contents)
      if item.head then s = "\\textbf{" .. s .. "}" end
      cells[c] = s
    end
    lines[#lines + 1] = table.concat(cells, " & ") .. " \\\\" .. (item.head and " \\hline" or "")
  end

  local env = wide and "table*" or "table"
  local open = use_x and ("\\begin{tabularx}{" .. width .. "}{" .. table.concat(spec) .. "}")
                      or ("\\begin{tabular}{" .. table.concat(spec) .. "}")
  local close = use_x and "\\end{tabularx}" or "\\end{tabular}"
  return table.concat({
    "\\begin{" .. env .. "}[!t]",
    "\\centering\\footnotesize",
    "\\caption{" .. caption .. "}",
    "\\label{" .. tables[roman] .. "}",
    "\\setlength{\\tabcolsep}{" .. (wide and "4pt" or "3pt") .. "}",
    open, "\\hline", table.concat(lines, "\n"), "\\hline", close,
    "\\end{" .. env .. "}",
  }, "\n")
end

function Pandoc(doc)
  chapter = stringify(doc.meta.chapter or "0")
  for k, v in stringify(doc.meta.refmap or ""):gmatch("(%d+)=([%w_-]+)") do refmap[k] = v end

  -- 1) bỏ danh sách tài liệu riêng của chương (dùng refs.bib chung)
  local blocks = pandoc.List()
  for _, b in ipairs(doc.blocks) do
    if b.t == "Header" and stringify(b.content):match("^Tài liệu tham khảo") then break end
    blocks:insert(b)
  end

  -- 2) gán nhãn cho bảng có caption "Bảng X."; caption (bỏ phần "Bảng X.") chuyển vào Div đánh dấu
  for i, b in ipairs(blocks) do
    local r = caption_roman(b)
    if r and blocks[i + 1] and blocks[i + 1].t == "Table" then
      tables[r] = "tab:c" .. chapter .. "-" .. r
      local cap = pandoc.List(b.content)
      cap:remove(1)
      while #cap > 0 and cap[1].t == "Space" do cap:remove(1) end
      blocks[i] = pandoc.Div({ pandoc.Plain(cap) }, pandoc.Attr("", {}, { { "caption-of", r } }))
    end
  end

  -- 3) trích dẫn, tham chiếu bảng/chương, ký hiệu toán, liên kết nội bộ
  doc.blocks = blocks
  doc = doc:walk({ Inlines = fix_inlines })
  blocks = doc.blocks

  -- 4) tiêu đề, bảng, công thức
  local out = pandoc.List()
  local i = 1
  while i <= #blocks do
    local b = blocks[i]
    if b.t == "Header" then
      local title = strip_heading(stringify(b.content))
      local level = ({ "section", "subsection", "subsubsection", "paragraph" })[b.level] or "paragraph"
      local label = b.level == 1 and ("\\label{sec:ch" .. chapter .. "}") or ""
      local esc = latex_inlines(pandoc.Inlines(title))
      out:insert(pandoc.RawBlock("latex", "\\" .. level .. "{" .. esc .. "}" .. label))
      i = i + 1
    elseif b.t == "Div" and b.attributes["caption-of"] and blocks[i + 1] and blocks[i + 1].t == "Table" then
      local r = b.attributes["caption-of"]
      out:insert(pandoc.RawBlock("latex", render_table(blocks[i + 1], r, latex(b.content))))
      i = i + 2
    elseif b.t == "Table" then
      error("Bảng không có caption \"**Bảng X.**\" ở chương " .. chapter)
    elseif b.t == "Para" and #b.content == 1 and b.content[1].t == "Math" and b.content[1].mathtype == "DisplayMath" then
      out:insert(pandoc.RawBlock("latex", "\\begin{equation}\n" .. b.content[1].text .. "\n\\end{equation}"))
      i = i + 1
    else
      out:insert(b)
      i = i + 1
    end
  end
  doc.blocks = out
  return doc
end
