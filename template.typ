// template.typ: generic book layout. Uses only fonts that Typst bundles.
// Usage: #show: book.with(title: "…", author: "…")

#let book(
  title: "Untitled",
  author: "",
  year: datetime.today().year(),
  width: 5.5in,
  height: 8.5in,
  inner: 0.875in,  // margin at the spine
  outer: 0.625in,
  top: 0.75in,
  bottom: 0.875in,
  font: "Libertinus Serif",
  size: 11pt,
  body,
) = {
  set document(title: title, author: author)
  set text(font: font, size: size, lang: "en")
  set par(justify: true, leading: 0.65em, first-line-indent: (amount: 1.2em, all: false), spacing: 0.65em)
  set page(
    width: width, height: height,
    margin: (inside: inner, outside: outer, top: top, bottom: bottom),
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
  pagebreak(weak: true, to: "odd")
  counter(page).update(1)
  set page(
    numbering: "1",
    header: context {
      let here = here().page()
      // No running head on a chapter's first page.
      if query(heading.where(level: 1)).any(h => h.location().page() == here) { return }
      set text(size: 0.85em, style: "italic")
      if calc.even(here) { author } else {
        let hs = query(heading.where(level: 1).before(here()))
        if hs.len() > 0 { align(right, hs.last().body) }
      }
    },
  )

  show heading.where(level: 1): it => {
    pagebreak(weak: true, to: "odd")
    v(5em)
    set par(first-line-indent: 0pt)
    text(size: 1.8em, weight: "bold", it.body)
    v(2.5em)
  }
  show heading.where(level: 2): it => {
    set par(first-line-indent: 0pt)
    v(1.4em, weak: true)
    text(size: 1.15em, weight: "bold", it.body)
    v(0.7em, weak: true)
  }
  show quote.where(block: true): set pad(x: 1.5em)
  show quote.where(block: true): set par(first-line-indent: 0pt)

  body
}
