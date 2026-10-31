// Verified example for dolanmiu/docx: basic formatting, CJK text, and stress tests.
// Copy this structure for a new document and change the content.
// Run from this folder: node example_qa_test.js  (writes example_qa_test.docx here)
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  Table, TableRow, TableCell, WidthType, ShadingType,
  PageBreak, AlignmentType, BorderStyle
} = require('docx');

const CJK_FONT = 'PingFang TC';
// A plain string font name only sets the ascii/hAnsi (Latin) font. Chinese text uses
// eastAsia, and when that is missing LibreOffice headless picks a random font
// (Kaiti, Xingkai, and other decorative faces). So fill in all three keys.
const FONT_OBJ = { ascii: CJK_FONT, eastAsia: CJK_FONT, hAnsi: CJK_FONT };

function makeRun(text, opts = {}) {
  return new TextRun({ text, font: FONT_OBJ, ...opts });
}

// --- Basic section: mixed font/color runs in ONE paragraph ---
const basicPara = new Paragraph({
  children: [
    makeRun('這是一段混合格式測試：', {}),
    makeRun('紅色粗體中文', { color: 'FF0000', bold: true }),
    makeRun('、', {}),
    // Never turn on the italics option anywhere in the document. Not only CJK runs: one italic
    // run, even pure Latin text, makes LibreOffice headless swap the CJK fonts of the
    // WHOLE document for decorative ones, and converting again does not help. For an
    // italic look in either script, use underline or a color instead.
    makeRun('藍色底線中文', { color: '0000FF', underline: {} }),
    makeRun(' English mixed ', { color: '0000FF', underline: {} }),
    makeRun('中英混排', { color: '0000FF', underline: {} }),
    makeRun('、以及一般文字收尾。', {}),
  ],
});

// --- Table: header shading + normal rows ---
function headerCell(text) {
  return new TableCell({
    shading: { type: ShadingType.CLEAR, fill: '4472C4' },
    children: [new Paragraph({ children: [makeRun(text, { color: 'FFFFFF', bold: true })] })],
    width: { size: 2000, type: WidthType.DXA },
  });
}
function dataCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [makeRun(text)] })],
    width: { size: 2000, type: WidthType.DXA },
  });
}

const basicTable = new Table({
  columnWidths: [2000, 2000, 2000, 2000],
  rows: [
    new TableRow({ children: [headerCell('項目'), headerCell('數量'), headerCell('單價'), headerCell('備註')] }),
    new TableRow({ children: [dataCell('測試品項 A'), dataCell('12'), dataCell('$100'), dataCell('正常列')] }),
    new TableRow({ children: [dataCell(''), dataCell(''), dataCell(''), dataCell('空白儲存格測試')] }),
  ],
});

// --- Stress test 1: large table 50 rows x 8 cols ---
const stressRows = [];
const stressHeaderCells = [];
for (let c = 0; c < 8; c++) stressHeaderCells.push(headerCell(`欄${c + 1}`));
stressRows.push(new TableRow({ children: stressHeaderCells }));
for (let r = 0; r < 50; r++) {
  const cells = [];
  for (let c = 0; c < 8; c++) cells.push(dataCell(`R${r + 1}C${c + 1}`));
  stressRows.push(new TableRow({ children: cells }));
}
const stressColWidths = Array(8).fill(1250);
const stressTable = new Table({ columnWidths: stressColWidths, rows: stressRows });

// --- Stress test 2: one very long "word" (a long URL) to check overflow ---
const longWord = 'https://example.com/' + 'a'.repeat(300);
const overflowPara = new Paragraph({ children: [makeRun(longWord)] });

// --- Stress test 3: many paragraphs (a long document, about 300) ---
const longDocParas = [];
for (let i = 0; i < 300; i++) {
  longDocParas.push(new Paragraph({
    children: [makeRun(`第 ${i + 1} 段：這是壓力測試用的重複段落內容，混合中文與 English text ${i}。`)],
  }));
}

const doc = new Document({
  // Heading and Title styles are resolved separately and do not inherit the font of a
  // TextRun. Override them here, or LibreOffice swaps the font of headings at random
  // even when every makeRun sets eastAsia.
  styles: {
    default: {
      document: { run: { font: FONT_OBJ } },
      heading1: { run: { font: FONT_OBJ } },
      heading2: { run: { font: FONT_OBJ } },
      title: { run: { font: FONT_OBJ } },
    },
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 } }, // A4 in DXA (already the default, spelled out)
    },
    children: [
      new Paragraph({ text: 'DOCX QA 測試文件', heading: HeadingLevel.HEADING_1 }),
      new Paragraph({ text: '一、基礎格式測試', heading: HeadingLevel.HEADING_2 }),
      basicPara,
      new Paragraph({ text: '' }),
      basicTable,
      new Paragraph({ children: [new PageBreak()] }),
      new Paragraph({ text: '二、邊角案例測試', heading: HeadingLevel.HEADING_2 }),
      overflowPara,
      new Paragraph({ children: [new PageBreak()] }),
      new Paragraph({ text: '三、大表格壓力測試（50x8）', heading: HeadingLevel.HEADING_2 }),
      stressTable,
      new Paragraph({ children: [new PageBreak()] }),
      new Paragraph({ text: '四、長文件壓力測試（300 段）', heading: HeadingLevel.HEADING_2 }),
      ...longDocParas,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync('example_qa_test.docx', buf);
  console.log('OK wrote example_qa_test.docx, bytes=', buf.length);
}).catch((e) => {
  console.error('FAIL', e);
  process.exit(1);
});
