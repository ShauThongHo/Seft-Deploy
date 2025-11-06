package com.invoice.service;

import com.invoice.model.Company;
import com.invoice.model.Invoice;
import com.invoice.model.InvoiceItem;
import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.borders.Border;
import com.itextpdf.layout.borders.SolidBorder;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;
import com.itextpdf.layout.properties.VerticalAlignment;

import java.io.FileOutputStream;
import java.text.DecimalFormat;
import java.time.format.DateTimeFormatter;

/**
 * 收据PDF生成器
 * Receipt PDF Generator Service
 */
public class PDFGeneratorNew {

    private static final DecimalFormat CURRENCY_FORMAT = new DecimalFormat("RM#,##0.00");
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("dd MMM yyyy");

    /**
     * 生成PDF收据
     */
    public void generatePDF(Invoice invoice, String outputPath) throws Exception {
        PdfWriter writer = new PdfWriter(new FileOutputStream(outputPath));
        PdfDocument pdf = new PdfDocument(writer);
        Document document = new Document(pdf);
        document.setMargins(40, 40, 40, 40);

        // 顶部：RECEIPT标题和公司信息
        addReceiptHeader(document, invoice);

        // Received From 信息
        addReceivedFromInfo(document, invoice);

        // 项目表格
        addItemsTable(document, invoice);

        // 底部总计
        addTotalsSection(document, invoice);

        // 应付金额
        addAmountDue(document, invoice);
        
        document.close();
    }

    /**
     * 添加收据头部（RECEIPT + 公司信息）
     */
    private void addReceiptHeader(Document document, Invoice invoice) {
        Table headerTable = new Table(new float[]{1, 1});
        headerTable.setWidth(UnitValue.createPercentValue(100));
        headerTable.setBorder(Border.NO_BORDER);

        // 左侧：RECEIPT标题
        Cell leftCell = new Cell()
                .add(new Paragraph("RECEIPT")
                        .setFontSize(32)
                        .setBold())
                .setBorder(Border.NO_BORDER)
                .setVerticalAlignment(VerticalAlignment.TOP);
        headerTable.addCell(leftCell);

        // 右侧：公司信息和Logo位置
        Company seller = invoice.getSeller();
        Cell rightCell = new Cell()
                .setBorder(Border.NO_BORDER)
                .setTextAlignment(TextAlignment.RIGHT);
        
        // Logo占位框
        rightCell.add(new Paragraph("[LOGO]")
                .setFontSize(10)
                .setBorder(new SolidBorder(1))
                .setPadding(20)
                .setTextAlignment(TextAlignment.CENTER)
                .setMarginBottom(10));
        
        if (seller != null) {
            rightCell.add(new Paragraph(seller.getName()).setBold().setFontSize(12));
            if (seller.getEmail() != null && !seller.getEmail().isEmpty()) {
                rightCell.add(new Paragraph(seller.getEmail()).setFontSize(9));
            }
        }
        
        headerTable.addCell(rightCell);
        document.add(headerTable);
        document.add(new Paragraph("\n"));
    }

    /**
     * 添加 Received From 信息
     */
    private void addReceivedFromInfo(Document document, Invoice invoice) {
        Company buyer = invoice.getBuyer();
        
        // Received From 和 Receipt Number/Date 表格
        Table infoTable = new Table(new float[]{2, 1});
        infoTable.setWidth(UnitValue.createPercentValue(100));
        infoTable.setMarginBottom(20);

        // 左侧：Received From
        Cell leftCell = new Cell()
                .setBorder(Border.NO_BORDER);
        leftCell.add(new Paragraph("Received From").setBold().setFontSize(10));
        leftCell.add(new Paragraph(buyer != null ? buyer.getName() : "")
                .setFontSize(14).setBold());
        if (buyer != null && buyer.getEmail() != null) {
            leftCell.add(new Paragraph(buyer.getEmail()).setFontSize(9));
        }
        infoTable.addCell(leftCell);

        // 右侧：Receipt Number 和日期
        Cell rightCell = new Cell()
                .setBorder(Border.NO_BORDER)
                .setTextAlignment(TextAlignment.RIGHT);
        rightCell.add(new Paragraph("RECEIPT NUMBER")
                .setFontSize(9).setBold());
        rightCell.add(new Paragraph(invoice.getInvoiceNumber())
                .setFontSize(12));
        rightCell.add(new Paragraph("\n"));
        rightCell.add(new Paragraph("日期 (Date)")
                .setFontSize(9).setBold());
        rightCell.add(new Paragraph(invoice.getInvoiceDate().format(DATE_FORMAT))
                .setFontSize(12));
        infoTable.addCell(rightCell);

        document.add(infoTable);
    }

    /**
     * 添加项目表格
     */
    private void addItemsTable(Document document, Invoice invoice) {
        // 表格：项目 | 价格 | 数量 | 金额
        Table table = new Table(new float[]{3, 1, 1, 1.5f});
        table.setWidth(UnitValue.createPercentValue(100));
        table.setMarginBottom(10);

        // 表头
        table.addHeaderCell(createHeaderCell("项目 (Item)"));
        table.addHeaderCell(createHeaderCell("价格 (Price)"));
        table.addHeaderCell(createHeaderCell("数量 (Qty)"));
        table.addHeaderCell(createHeaderCell("金额 (Amount)"));

        // 项目行
        for (InvoiceItem item : invoice.getItems()) {
            table.addCell(createBodyCell(item.getName(), TextAlignment.LEFT));
            table.addCell(createBodyCell(CURRENCY_FORMAT.format(item.getUnitPrice()), TextAlignment.RIGHT));
            table.addCell(createBodyCell(String.valueOf(item.getQuantity()), TextAlignment.CENTER));
            table.addCell(createBodyCell(CURRENCY_FORMAT.format(item.getSubtotal()), TextAlignment.RIGHT));
        }

        document.add(table);
    }

    /**
     * 添加总计部分
     */
    private void addTotalsSection(Document document, Invoice invoice) {
        double subtotal = invoice.getTotalSubtotal();
        double total = invoice.getGrandTotal();

        Table totalsTable = new Table(new float[]{3, 1.5f});
        totalsTable.setWidth(UnitValue.createPercentValue(100));
        totalsTable.setBorder(Border.NO_BORDER);

        // 小计
        totalsTable.addCell(createNoBorderCell("小计 (Subtotal)", TextAlignment.RIGHT));
        totalsTable.addCell(createNoBorderCell(CURRENCY_FORMAT.format(subtotal), TextAlignment.RIGHT));

        // 总计
        totalsTable.addCell(createNoBorderCell("总计 (Total)", TextAlignment.RIGHT).setBold());
        totalsTable.addCell(createNoBorderCell(CURRENCY_FORMAT.format(total), TextAlignment.RIGHT).setBold());

        // 支付日期
        totalsTable.addCell(createNoBorderCell("支付日期 (Payment Date): " + 
                invoice.getInvoiceDate().format(DATE_FORMAT), TextAlignment.RIGHT));
        totalsTable.addCell(createNoBorderCell(CURRENCY_FORMAT.format(total), TextAlignment.RIGHT));

        document.add(totalsTable);
    }

    /**
     * 添加应付金额（底部大字显示）
     */
    private void addAmountDue(Document document, Invoice invoice) {
        document.add(new Paragraph("\n\n"));
        
        Table amountTable = new Table(new float[]{1, 1});
        amountTable.setWidth(UnitValue.createPercentValue(100));
        amountTable.setBorder(Border.NO_BORDER);

        // 左侧：应付金额标签
        amountTable.addCell(createNoBorderCell("应付金额 (Amount Due)", TextAlignment.LEFT)
                .setFontSize(14).setBold());

        // 右侧：金额
        amountTable.addCell(createNoBorderCell(CURRENCY_FORMAT.format(invoice.getGrandTotal()), 
                TextAlignment.RIGHT)
                .setFontSize(20).setBold());

        document.add(amountTable);
    }

    /**
     * 创建表头单元格
     */
    private Cell createHeaderCell(String content) {
        return new Cell()
                .add(new Paragraph(content).setFontSize(10).setBold())
                .setBackgroundColor(new DeviceRgb(240, 240, 240))
                .setPadding(8)
                .setTextAlignment(TextAlignment.CENTER);
    }

    /**
     * 创建表体单元格
     */
    private Cell createBodyCell(String content, TextAlignment alignment) {
        return new Cell()
                .add(new Paragraph(content).setFontSize(10))
                .setPadding(8)
                .setTextAlignment(alignment);
    }

    /**
     * 创建无边框单元格
     */
    private Cell createNoBorderCell(String content, TextAlignment alignment) {
        return new Cell()
                .add(new Paragraph(content).setFontSize(10))
                .setBorder(Border.NO_BORDER)
                .setPadding(5)
                .setTextAlignment(alignment);
    }
}
