package com.invoice.model;

/**
 * 公司信息模型
 * Company Information Model
 */
public class Company {
    private String name;        // 公司名称
    private String address;     // 地址
    private String taxId;       // 税号
    private String phone;       // 电话
    private String email;       // 邮箱

    public Company() {
    }

    public Company(String name, String address, String taxId, String phone, String email) {
        this.name = name;
        this.address = address;
        this.taxId = taxId;
        this.phone = phone;
        this.email = email;
    }

    // Getters and Setters
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getTaxId() {
        return taxId;
    }

    public void setTaxId(String taxId) {
        this.taxId = taxId;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
