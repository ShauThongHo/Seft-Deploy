package com.invoice.test;

import com.invoice.model.Company;
import com.invoice.model.Invoice;
import com.invoice.model.InvoiceItem;
import com.invoice.service.PDFGenerator;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 测试收据生成
 */
public class TestReceiptGeneration {
    public static void main(String[] args) {
        try {
            // 创建收据
            Invoice receipt = new Invoice();
            receipt.setInvoiceNumber("SUCCeSS-23A-102");
            receipt.setInvoiceDate(LocalDate.of(2025, 10, 30));
            receipt.setNotes("");

            // 收款方 (Seller)
            Company seller = new Company(
                "SUC Computer Science Society",
                "Sunway University",
                "",
                "+60-3-12345678",
                "suc.cess.2021.IT@gmail.com"
            );
            receipt.setSeller(seller);

            // 付款方 (Buyer / Received From)
            Company buyer = new Company(
                "Bryan Ang Duo En",
                "",
                "",
                "",
                "d25037c@isc.edu.my"
            );
            receipt.setBuyer(buyer);

            // 添加项目
            InvoiceItem item = new InvoiceItem(
                "Membership Fee 2025 (Diploma)",
                1,
                20.00,
                0.0
            );
            receipt.getItems().add(item);

            // 标记为已付款 20.00，使应付金额显示为 0.00（与示例相符）
            receipt.setPaidAmount(20.00);

            // 生成PDF
            PDFGenerator generator = new PDFGenerator();
            String desktopPath = System.getProperty("user.home") + "\\Desktop\\";
            String outputPath = desktopPath + "TestReceipt_" + 
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")) + ".pdf";
            
            generator.generatePDF(receipt, outputPath);
            
            System.out.println("=================================");
            System.out.println("收据生成成功！");
            System.out.println("文件位置: " + outputPath);
            System.out.println("=================================");
            
        } catch (Exception e) {
            System.err.println("生成收据时出错:");
            e.printStackTrace();
        }
    }
}
