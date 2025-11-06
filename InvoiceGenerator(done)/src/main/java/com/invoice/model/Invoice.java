package com.invoice.model;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * 发票模型
 * Invoice Model
 */
public class Invoice {
    private String invoiceNumber;       // 发票编号
    private LocalDate invoiceDate;      // 发票日期
    private Company seller;             // 卖方信息
    private Company buyer;              // 买方信息
    private List<InvoiceItem> items;    // 商品列表
    private String notes;               // 备注
    private double paidAmount;          // 已付款金额

    public Invoice() {
        this.items = new ArrayList<>();
        this.invoiceDate = LocalDate.now();
        this.paidAmount = 0.0;
    }

    // Getters and Setters
    public String getInvoiceNumber() {
        return invoiceNumber;
    }

    public void setInvoiceNumber(String invoiceNumber) {
        this.invoiceNumber = invoiceNumber;
    }

    public LocalDate getInvoiceDate() {
        return invoiceDate;
    }

    public void setInvoiceDate(LocalDate invoiceDate) {
        this.invoiceDate = invoiceDate;
    }

    public Company getSeller() {
        return seller;
    }

    public void setSeller(Company seller) {
        this.seller = seller;
    }

    public Company getBuyer() {
        return buyer;
    }

    public void setBuyer(Company buyer) {
        this.buyer = buyer;
    }

    public List<InvoiceItem> getItems() {
        return items;
    }

    public void setItems(List<InvoiceItem> items) {
        this.items = items;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public double getPaidAmount() {
        return paidAmount;
    }

    public void setPaidAmount(double paidAmount) {
        this.paidAmount = paidAmount;
    }

    /**
     * 添加商品项目
     */
    public void addItem(InvoiceItem item) {
        items.add(item);
    }

    /**
     * 移除商品项目
     */
    public void removeItem(int index) {
        if (index >= 0 && index < items.size()) {
            items.remove(index);
        }
    }

    /**
     * 计算总小计（不含税）
     */
    public double getTotalSubtotal() {
        return items.stream()
                .mapToDouble(InvoiceItem::getSubtotal)
                .sum();
    }

    /**
     * 计算总税额
     */
    public double getTotalTax() {
        return items.stream()
                .mapToDouble(InvoiceItem::getTaxAmount)
                .sum();
    }

    /**
     * 计算总金额（含税）
     */
    public double getGrandTotal() {
        return getTotalSubtotal() + getTotalTax();
    }
}
