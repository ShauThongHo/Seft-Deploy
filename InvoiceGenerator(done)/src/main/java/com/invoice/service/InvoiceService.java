package com.invoice.service;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import com.invoice.model.Invoice;

import java.io.*;
import java.lang.reflect.Type;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * 发票服务
 * Invoice Service
 */
public class InvoiceService {

    private static final String DATA_FILE = "invoices_data.json";
    private final Gson gson;

    public InvoiceService() {
        this.gson = new GsonBuilder()
                .registerTypeAdapter(LocalDate.class, new LocalDateAdapter())
                .setPrettyPrinting()
                .create();
    }

    /**
     * 保存发票
     */
    public void saveInvoice(Invoice invoice) throws IOException {
        List<Invoice> invoices = loadAllInvoices();
        invoices.add(invoice);
        
        try (Writer writer = new FileWriter(DATA_FILE)) {
            gson.toJson(invoices, writer);
        }
    }

    /**
     * 加载所有发票
     */
    public List<Invoice> loadAllInvoices() {
        File file = new File(DATA_FILE);
        if (!file.exists()) {
            return new ArrayList<>();
        }

        try (Reader reader = new FileReader(file)) {
            Type listType = new TypeToken<List<Invoice>>(){}.getType();
            List<Invoice> invoices = gson.fromJson(reader, listType);
            return invoices != null ? invoices : new ArrayList<>();
        } catch (IOException e) {
            e.printStackTrace();
            return new ArrayList<>();
        }
    }
}
