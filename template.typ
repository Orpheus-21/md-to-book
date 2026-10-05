// template.typ: generic book layout. Uses only fonts that Typst bundles.
// Usage: #show: book.with(title: "…", author: "…")

#let book(
  title: "Untitled",
  author: "",
  year: datetime.today().year(),
  width: 5.5in,
  height: 8.5in,
  bleed: 0pt,      // extra paper on the top, bottom, and outer edges
  inner: 0.875in,  // margin at the spine
  outer: 0.625in,
  top: 0.75in,
  bottom: 0.875in,
  font: "Libertinus Serif",
  size: 11pt,
  lang: "en",
  body,
) = {
  set document(title: title, author: author)
  set text(font: font, size: size, lang: lang)
  set par(justify: true, leading: 0.65em, first-line-indent: (amount: 1.2em, all: false), spacing: 0.65em)
  set page(
    width: width + bleed, height: height + 2 * bleed,
    margin: (inside: inner, outside: outer + bleed, top: top + bleed, bottom: bottom + bleed),
  )

  // Title page: no number, no running head.
  page(numbering: none, header: none)[
    #v(1fr)
    #align(center)[
      #text(size: 2.4em, weight: "bold")[#title]
      #v(1.5em)
      #text(size: 1.3em)[#author]
    ]
    #v(2fr)
  ]

  // Copyright page.
  page(header: none)[
    #v(1fr)
    #set par(first-line-indent: 0pt)
    #set text(size: 0.85em)
    © #year #author. All rights reserved.
  ]

  // Table of contents.
  page(header: none)[
    #set par(first-line-indent: 0pt)
    #outline(title: [Contents], depth: 1)
  ]

  // Chapters start on a right-hand page. Page numbers start at 1 there.
  // A chapter-end marker sits at the end of each chapter. A page is blank when
  // the page before it holds a marker and the page after it opens a chapter.
  pagebreak(weak: true, to: "odd")
  counter(page).update(1)
  let blank() = {
    let p = here().page()
    let after-end = query(<chapter-end>).any(m => m.location().page() == p - 1)
    let before-chapter = query(heading.where(level: 1)).any(h => h.location().page() == p + 1)
    after-end and before-chapter
  }
  set page(
    header: context {
      let p = here().page()
      if blank() or query(heading.where(level: 1)).any(h => h.location().page() == p) { return }
      set text(size: 0.85em, style: "italic")
      if calc.even(p) { author } else {
        let hs = query(heading.where(level: 1).before(here()))
        if hs.len() > 0 { align(right, hs.last().body) }
      }
    },
    footer: context if not blank() { align(center, counter(page).display("1")) },
  )

  show heading.where(level: 1): it => {
    [#metadata(none) <chapter-end>]
    pagebreak(weak: true, to: "odd")
    v(4em)
    set par(first-line-indent: 0pt)
    it
    v(1.5em)
  }
  show heading.where(level: 1): set text(size: 1.8em, weight: "bold")
  show heading.where(level: 2): set text(size: 1.15em, weight: "bold")
  show heading.where(level: 2): set block(above: 1.4em, below: 0.7em)
  show heading: set par(first-line-indent: 0pt)
  // Tables: rules above the header, below the header, and below the last row. Bold header.
  set table(stroke: (_, y) => (top: if y == 0 { 0.8pt } else if y == 1 { 0.4pt } else { 0pt }))
  show table: set text(size: 0.9em)
  show table: set par(first-line-indent: 0pt, justify: false)
  show table: it => block(stroke: (bottom: 0.8pt), it)
  show table.cell.where(y: 0): strong
  show quote.where(block: true): set pad(x: 1.5em)
  show quote.where(block: true): set par(first-line-indent: 0pt)

  body

  // The query `typst query main.typ "<npages>"` reads the last page number.
  context [#metadata(here().page()) <npages>]
}
