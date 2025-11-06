package com.invoice.model;

/**
 * 发票项目模型
 * Invoice Item Model
 */
public class InvoiceItem {
    private String name;           // 商品名称
    private int quantity;          // 数量
    private double unitPrice;      // 单价
    private double taxRate;        // 税率 (%)

    public InvoiceItem() {
    }

    public InvoiceItem(String name, int quantity, double unitPrice, double taxRate) {
        this.name = name;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
        this.taxRate = taxRate;
    }

    // Getters and Setters
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    public double getUnitPrice() {
        return unitPrice;
    }

    public void setUnitPrice(double unitPrice) {
        this.unitPrice = unitPrice;
    }

    public double getTaxRate() {
        return taxRate;
    }

    public void setTaxRate(double taxRate) {
        this.taxRate = taxRate;
    }

    /**
     * 计算小计（不含税）
     */
    public double getSubtotal() {
        return quantity * unitPrice;
    }

    /**
     * 计算税额
     */
    public double getTaxAmount() {
        return getSubtotal() * (taxRate / 100.0);
    }

    /**
     * 计算总计（含税）
     */
    public double getTotal() {
        return getSubtotal() + getTaxAmount();
    }
}
