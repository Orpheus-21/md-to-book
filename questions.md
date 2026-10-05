# Questions to ask before a build

Ask one question at a time. Give the default with each question. Stop when you have the answers in the table at the end.

## 1. Always ask

1. **Title and author.** Ask for both. There is no default.
2. **Reading order.** Run `python3 build.py DIR --list`. Show the list. Ask: "Is this the order you want?" If not, collect the new order and use `--files`.
3. **Endgame.** Ask: "Is the book for the screen or for print?"
   * If the user asks for EPUB, say that this tool does not make EPUB. Offer a screen PDF.

## 2. Screen PDF

4. **Page size.** Default: `6x9`. Other choices: `a5`, `a4`, `5.5x8.5`.
5. **Font size.** Do not ask. Use the default `11pt`. Change it only if the user asks.

## 3. Print book

4. **Binding.** This version makes paperback books only. If the user wants a hardcover, say so and stop.
5. **Printer.** Ask: "Which printer or service?" Default: KDP.
   * KDP: the rules are known. Use `--print`.
   * Another printer: ask the user for the printer spec sheet. Ask for the trim sizes, the bleed, and the inside margin by page count. Build with `--trim` and `--bleed`. Say that the margin check applies to KDP only.
6. **Trim size.** Default: `6x9`. Common KDP sizes: `5x8`, `5.25x8`, `5.5x8.5`, `6x9`.
7. **Bleed.** Ask: "Does any image touch the edge of the page?" If no, use no bleed. If yes, use `--bleed 0.125in`.

## 4. Answer to flag

| Answer | Flag |
|---|---|
| Title, author | `--title`, `--author` |
| Order | `--files a.md b.md` |
| Page or trim size | `--trim 6x9` |
| Print book on KDP | `--print` |
| Image bleed | `--bleed 0.125in` |
| Font size | `--font-size 11pt` |

After the build, tell the user the page count, which the script prints. For print, tell the user the inside margin that the script chose.
