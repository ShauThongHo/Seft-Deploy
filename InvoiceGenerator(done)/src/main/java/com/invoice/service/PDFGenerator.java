package com.invoice.service;

import com.invoice.model.Company;
import com.invoice.model.Invoice;
import com.invoice.model.InvoiceItem;
import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.io.image.ImageData;
import com.itextpdf.io.image.ImageDataFactory;
import com.itextpdf.layout.element.Image;
import com.itextpdf.layout.properties.HorizontalAlignment;
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
public class PDFGenerator {

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

        // 左侧：RECEIPT 标题和卖方公司名称 + 邮箱（与示例一致，RECEIPT 大标题）
        Cell leftCell = new Cell()
                .add(new Paragraph("RECEIPT").setFontSize(34).setBold())
                .add(new Paragraph(invoice.getSeller() != null ? invoice.getSeller().getName() : "").setFontSize(14).setBold().setMarginTop(6))
                .add(new Paragraph(invoice.getSeller() != null && invoice.getSeller().getEmail() != null ? invoice.getSeller().getEmail() : "").setFontSize(9).setFontColor(ColorConstants.GRAY))
                .setBorder(Border.NO_BORDER)
                .setVerticalAlignment(VerticalAlignment.TOP);
        headerTable.addCell(leftCell);

        // 右侧：Logo 占位和小号公司名（右对齐）
        Company seller = invoice.getSeller();
        Cell rightCell = new Cell()
                .setBorder(Border.NO_BORDER)
                .setTextAlignment(TextAlignment.RIGHT)
                .setVerticalAlignment(VerticalAlignment.TOP);

        // 尝试加载 resources 下的 logo（路径: /img/logo.png），否则保留占位符
        try {
            java.io.InputStream is = PDFGenerator.class.getResourceAsStream("/img/logo.png");
            if (is != null) {
                byte[] bytes = is.readAllBytes();
                ImageData imgData = ImageDataFactory.create(bytes);
                Image logo = new Image(imgData).scaleToFit(140, 60);
                logo.setHorizontalAlignment(HorizontalAlignment.RIGHT);
                rightCell.add(logo);
            } else {
                rightCell.add(new Paragraph("[LOGO]")
                        .setFontSize(10)
                        .setBorder(new SolidBorder(1))
                        .setPadding(12)
                        .setTextAlignment(TextAlignment.CENTER)
                        .setMarginBottom(6));
            }
        } catch (Exception e) {
            rightCell.add(new Paragraph("[LOGO]")
                    .setFontSize(10)
                    .setBorder(new SolidBorder(1))
                    .setPadding(12)
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(6));
        }

        if (seller != null) {
            rightCell.add(new Paragraph(seller.getName()).setFontSize(10).setItalic());
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
        // 外层表格用于绘制带边框的区域，模拟附图中的白色圆角卡片效果
        Table outer = new Table(new float[]{1});
        outer.setWidth(UnitValue.createPercentValue(100));
        outer.setMarginBottom(18);

    Cell outerCell = new Cell().setBorder(new SolidBorder(new DeviceRgb(220,220,220), 1)).setPadding(12);

        Table inner = new Table(new float[]{2, 1});
        inner.setWidth(UnitValue.createPercentValue(100));

        // 左侧：Received From
        Cell leftCell = new Cell().setBorder(Border.NO_BORDER);
        leftCell.add(new Paragraph("Received From").setFontSize(9).setFontColor(ColorConstants.GRAY));
        leftCell.add(new Paragraph(buyer != null ? buyer.getName() : "").setFontSize(14).setBold());
        if (buyer != null && buyer.getEmail() != null && !buyer.getEmail().isEmpty()) {
            leftCell.add(new Paragraph(buyer.getEmail()).setFontSize(9).setFontColor(ColorConstants.GRAY));
        }
        inner.addCell(leftCell);

        // 右侧：Receipt Number 和日期（右对齐）
        Cell rightCell = new Cell().setBorder(Border.NO_BORDER).setTextAlignment(TextAlignment.RIGHT);
        rightCell.add(new Paragraph("RECEIPT NUMBER").setFontSize(9).setBold());
        rightCell.add(new Paragraph(invoice.getInvoiceNumber()).setFontSize(12));
        rightCell.add(new Paragraph("\n"));
    rightCell.add(new Paragraph("Date").setFontSize(9).setBold());
        rightCell.add(new Paragraph(invoice.getInvoiceDate().format(DATE_FORMAT)).setFontSize(12));
        inner.addCell(rightCell);

        outerCell.add(inner);
        outer.addCell(outerCell);
        document.add(outer);
    }

    /**
     * 添加项目表格
     */
    private void addItemsTable(Document document, Invoice invoice) {
        // 表格：项目 | 价格 | 数量 | 金额
        Table table = new Table(new float[]{3, 1, 1, 1.5f});
        table.setWidth(UnitValue.createPercentValue(100));
        table.setMarginBottom(10);

    // Table header (English)
    table.addHeaderCell(createHeaderCell("Item"));
    table.addHeaderCell(createHeaderCell("Price"));
    table.addHeaderCell(createHeaderCell("Qty"));
    table.addHeaderCell(createHeaderCell("Amount"));

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
        double paid = invoice.getPaidAmount();
        // If paid amount is not provided (0 or negative), assume fully paid at time of receipt generation
        if (paid <= 0.0) {
            paid = total;
        }
    // amountDue will be computed/used in the bottom section
                // 将 totals 放在右侧小块区域，使用嵌套表格实现右侧对齐效果
                Table outer = new Table(new float[]{3, 1});
                outer.setWidth(UnitValue.createPercentValue(100));
                outer.setBorder(Border.NO_BORDER);

                // 左侧空白占位
                outer.addCell(new Cell().setBorder(Border.NO_BORDER));

                // 右侧嵌套表格：小计/总计/支付日期
                Table right = new Table(new float[]{1, 1});
                right.setWidth(UnitValue.createPercentValue(100));

            // Subtotal
            right.addCell(createNoBorderCell("Subtotal", TextAlignment.RIGHT));
            right.addCell(createNoBorderCell(CURRENCY_FORMAT.format(subtotal), TextAlignment.RIGHT));

            // Total
            right.addCell(createNoBorderCell("Total", TextAlignment.RIGHT).setBold());
            right.addCell(createNoBorderCell(CURRENCY_FORMAT.format(total), TextAlignment.RIGHT).setBold());

            // Amount Paid
            right.addCell(createNoBorderCell("Amount Paid", TextAlignment.RIGHT));
            right.addCell(createNoBorderCell(CURRENCY_FORMAT.format(paid), TextAlignment.RIGHT));

            // Payment Date (display)
            right.addCell(createNoBorderCell("Payment Date: " + invoice.getInvoiceDate().format(DATE_FORMAT), TextAlignment.RIGHT));
            right.addCell(createNoBorderCell("", TextAlignment.RIGHT));

                Cell rightCell = new Cell().setBorder(Border.NO_BORDER).add(right);
                outer.addCell(rightCell);

                document.add(outer);
    }

    /**
     * 添加应付金额（底部大字显示）
     */
    private void addAmountDue(Document document, Invoice invoice) {
        document.add(new Paragraph("\n\n"));
        
        // 底部大额显示，右侧金额加粗放大
        Table outer = new Table(new float[]{3, 1});
        outer.setWidth(UnitValue.createPercentValue(100));
        outer.setBorder(Border.NO_BORDER);

        // 左侧空白
        outer.addCell(new Cell().setBorder(Border.NO_BORDER));

    // 右侧显示：應付金額 与金额（计算：总计 - 已付款）
        Table right = new Table(new float[]{1, 1});
        right.setWidth(UnitValue.createPercentValue(100));
        double total = invoice.getGrandTotal();
        double paid = invoice.getPaidAmount();
        if (paid <= 0.0) {
            // default to fully paid when generating a receipt
            paid = total;
        }
        double amountDue = total - paid;

    right.addCell(createNoBorderCell("Amount Paid", TextAlignment.LEFT).setFontSize(12));
    right.addCell(createNoBorderCell(CURRENCY_FORMAT.format(paid), TextAlignment.RIGHT).setFontSize(12));

    // Large Amount Due display
    right.addCell(createNoBorderCell("Amount Due", TextAlignment.LEFT).setFontSize(12).setBold());
    right.addCell(createNoBorderCell(CURRENCY_FORMAT.format(amountDue), TextAlignment.RIGHT).setFontSize(22).setBold());

        outer.addCell(new Cell().setBorder(Border.NO_BORDER).add(right));
        document.add(outer);
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
