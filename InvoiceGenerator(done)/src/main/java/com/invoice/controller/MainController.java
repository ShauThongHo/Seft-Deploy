package com.invoice.controller;

import com.invoice.model.Company;
import com.invoice.model.Invoice;
import com.invoice.model.InvoiceItem;
import com.invoice.service.InvoiceService;
import com.invoice.service.PDFGenerator;
import javafx.animation.TranslateTransition;
import javafx.animation.FadeTransition;
import javafx.animation.ParallelTransition;
import javafx.util.Duration;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.layout.VBox;
import javafx.scene.layout.HBox;
import javafx.scene.layout.StackPane;
import javafx.geometry.Pos;
import javafx.stage.FileChooser;
import javafx.stage.DirectoryChooser;

import java.io.File;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;

/**
 * 主控制器
 * Main Controller
 */
public class MainController {

    // Navigation & Pages
    @FXML private StackPane contentStack;
    @FXML private VBox pageGenerate;
    @FXML private VBox pageSellerInfo;
    @FXML private VBox pageSalesItems;
    @FXML private Button navGenerate;
    @FXML private Button navSellerInfo;
    @FXML private Button navSalesItems;
    @FXML private Button navExport;
    
    // Generate Page Mode Toggle
    @FXML private StackPane modeStack;
    @FXML private VBox modeSingle;
    @FXML private VBox modeBulk;
    @FXML private Button modeButtonSingle;
    @FXML private Button modeButtonBulk;
    
    // Track current mode to prevent redundant animations
    private boolean isSingleMode = true;
    
    // 基本信息
    @FXML private TextField invoiceNumberField;
    @FXML private DatePicker invoiceDatePicker;
    @FXML private TextArea notesArea;

    // 卖方信息
    @FXML private TextField sellerNameField;
    @FXML private TextArea sellerAddressField;
    @FXML private TextField sellerTaxIdField;
    @FXML private TextField sellerPhoneField;
    @FXML private TextField sellerEmailField;
    @FXML private Label logoFileLabel;
    @FXML private VBox logoPreviewBox;
    @FXML private VBox receiptPreviewBox;
    
    // Logo file path
    private String logoFilePath = null;
    
    // defaults file location
    private final File defaultsFile = new File(System.getProperty("user.home"), ".invoice_generator_defaults.properties");
    private final File savedItemsFile = new File(System.getProperty("user.home"), ".invoice_generator_items.json");
    // next invoice counter to use (1..9999). We store the "next to use" value in the properties file.
    private int invoiceCounter = 1;

    // 买方信息
    @FXML private TextField buyerNameField;
    @FXML private TextField buyerAddressField;
    @FXML private TextField buyerTaxIdField;
    @FXML private TextField buyerPhoneField;
    @FXML private TextField buyerEmailField;

    // 商品项目
    @FXML private TextField itemNameField;
    @FXML private TextField itemPriceField;
    @FXML private TextField itemTaxRateField;
    
    // Single Generate Items Table
    @FXML private TableView<InvoiceItem> singleItemsTable;
    @FXML private TableColumn<InvoiceItem, String> singleNameColumn;
    @FXML private TableColumn<InvoiceItem, Integer> singleQuantityColumn;
    @FXML private TableColumn<InvoiceItem, Double> singlePriceColumn;
    @FXML private TableColumn<InvoiceItem, Double> singleTotalColumn;
    @FXML private Label singleTotalLabel;
    
    // Bulk Generate Items Table
    @FXML private TableView<InvoiceItem> bulkItemsTable;
    @FXML private TableColumn<InvoiceItem, String> bulkNameColumn2;
    @FXML private TableColumn<InvoiceItem, Integer> bulkQuantityColumn;
    @FXML private TableColumn<InvoiceItem, Double> bulkPriceColumn;
    @FXML private TableColumn<InvoiceItem, Double> bulkTotalColumn;
    @FXML private Label bulkTotalLabel;

    // Legacy fields (kept for compatibility)
    @FXML private Label subtotalLabel;
    @FXML private Label taxLabel;
    @FXML private Label totalLabel;
    @FXML private CheckBox paidCheckBox;
    @FXML private TableView<BulkBuyer> bulkTable;
    @FXML private TableColumn<BulkBuyer, String> bulkNameColumn;
    @FXML private TableColumn<BulkBuyer, String> bulkIdColumn;
    @FXML private TableColumn<BulkBuyer, String> bulkEmailColumn;
    @FXML private TableColumn<BulkBuyer, Void> bulkActionsColumn;
    @FXML private TextArea bulkNamesArea;
    @FXML private TextArea bulkIdsArea;
    @FXML private TextArea bulkEmailsArea;
    @FXML private TextField bulkNameField;
    @FXML private TextField bulkIdField;
    @FXML private TextField bulkEmailField;
    @FXML private Label bulkCountLabel;
    
    // Sales Items Page
    @FXML private VBox savedItemsContainer;

    private ObservableList<InvoiceItem> items = FXCollections.observableArrayList();
    private ObservableList<BulkBuyer> bulkList = FXCollections.observableArrayList();
    private ObservableList<InvoiceItem> savedItems = FXCollections.observableArrayList(); // 商品库存
    private InvoiceService invoiceService = new InvoiceService();
    private PDFGenerator pdfGenerator = new PDFGenerator();

    // simple sanitizer for filenames
    private String sanitizeFileName(String input) {
        if (input == null) return "buyer";
        String s = input.replaceAll("[^a-zA-Z0-9\\._-]", "_");
        return s.length() > 40 ? s.substring(0, 40) : s;
    }

    /**
     * Parse pasted lines (one per buyer) and add them to the bulk list.
     * Supported CSV per line: name,id,email or name,email (id optional). Commas inside fields are not supported.
     */
    @FXML
    private void handlePasteBulk() {
        // Column-mode: combine names/ids/emails pasted into the three separate boxes (one per line)
        if ((bulkNamesArea == null || bulkIdsArea == null || bulkEmailsArea == null)) return;

        String namesText = bulkNamesArea.getText();
        String idsText = bulkIdsArea.getText();
        String emailsText = bulkEmailsArea.getText();
        if ((namesText == null || namesText.trim().isEmpty())
                && (idsText == null || idsText.trim().isEmpty())
                && (emailsText == null || emailsText.trim().isEmpty())) {
            showAlert("Error", "Please paste names, ids or emails into the three boxes first", Alert.AlertType.ERROR);
            return;
        }

        String[] names = namesText == null ? new String[0] : namesText.split("\\r?\\n");
        String[] ids = idsText == null ? new String[0] : idsText.split("\\r?\\n");
        String[] emails = emailsText == null ? new String[0] : emailsText.split("\\r?\\n");

        int n = names.length;
        int m = ids.length;
        int e = emails.length;
        int max = Math.max(n, Math.max(m, e));

        int added = 0;
        for (int i = 0; i < max; i++) {
            String name = i < n ? names[i].trim() : "";
            String id = i < m ? ids[i].trim() : "";
            String email = i < e ? emails[i].trim() : "";
            if (name.isEmpty() && id.isEmpty() && email.isEmpty()) continue;
            bulkList.add(new BulkBuyer(name, id, email));
            added++;
        }

        // clear inputs
        bulkNamesArea.clear();
        bulkIdsArea.clear();
        bulkEmailsArea.clear();

        String msg = added + " buyers added to the Bulk list";
        if (n != m || n != e) {
            msg += "; note: column counts differed (names=" + n + ", ids=" + m + ", emails=" + e + ") — missing values were left blank";
        }
        showAlert("Info", msg, Alert.AlertType.INFORMATION);
        updateBulkCount();
    }

    /**
     * Add customers from Name and ID text areas (simplified version without email field)
     */
    @FXML
    private void handleAddBulkCustomers() {
        if (bulkNamesArea == null || bulkIdsArea == null) return;

        String namesText = bulkNamesArea.getText();
        String idsText = bulkIdsArea.getText();
        
        if ((namesText == null || namesText.trim().isEmpty()) 
                && (idsText == null || idsText.trim().isEmpty())) {
            showAlert("Error", "Please enter names and IDs", Alert.AlertType.ERROR);
            return;
        }

        String[] names = namesText == null ? new String[0] : namesText.split("\\r?\\n");
        String[] ids = idsText == null ? new String[0] : idsText.split("\\r?\\n");

        int n = names.length;
        int m = ids.length;
        int max = Math.max(n, m);

        int added = 0;
        for (int i = 0; i < max; i++) {
            String name = i < n ? names[i].trim() : "";
            String id = i < m ? ids[i].trim() : "";
            
            if (name.isEmpty() && id.isEmpty()) continue;
            
            // Auto-generate email: id@sc.edu.my
            String email = "";
            if (!id.isEmpty()) {
                email = id + "@sc.edu.my";
            }
            
            bulkList.add(new BulkBuyer(name, id, email));
            added++;
        }

        // Clear inputs
        bulkNamesArea.clear();
        bulkIdsArea.clear();

        String msg = added + " customers added to the list";
        if (n != m) {
            msg += "\nNote: Name count (" + n + ") and ID count (" + m + ") differ - missing values were left blank";
        }
        showAlert("Success", msg, Alert.AlertType.INFORMATION);
        updateBulkCount();
    }

    /**
     * Update the customer count label
     */
    private void updateBulkCount() {
        if (bulkCountLabel != null) {
            int count = bulkList.size();
            bulkCountLabel.setText(count + (count == 1 ? " customer" : " customers"));
        }
    }

    // simple holder for bulk buyer rows
    public static class BulkBuyer {
        private String name;
        private String id;
        private String email;

        public BulkBuyer() {}
        public BulkBuyer(String name, String id, String email) {
            this.name = name; this.id = id; this.email = email;
        }

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
    }

    @FXML
    public void initialize() {
        // Initialize page visibility - show Generate by default
        if (pageGenerate != null) pageGenerate.setVisible(true);
        if (pageSellerInfo != null) pageSellerInfo.setVisible(false);
        if (pageSalesItems != null) pageSalesItems.setVisible(false);
        
        // Initialize mode visibility - show Single mode by default
        if (modeSingle != null) modeSingle.setVisible(true);
        if (modeBulk != null) modeBulk.setVisible(false);
        
        // Style mode buttons
        if (modeButtonSingle != null) modeButtonSingle.getStyleClass().add("nav-btn-active");

        // 初始化发票编号和日期
        if (invoiceNumberField != null) invoiceNumberField.setText("");
        if (invoiceDatePicker != null) invoiceDatePicker.setValue(LocalDate.now());
        if (itemTaxRateField != null) itemTaxRateField.setText("0.0");

        // default: mark as paid
        if (paidCheckBox != null) {
            paidCheckBox.setSelected(true);
        }

        // 设置 Bulk Generate 的 promptText 换行 - 使用 Platform.runLater 确保在 UI 完全初始化后设置
        Platform.runLater(() -> {
            if (bulkNamesArea != null) {
                String namePrompt = "Micage Ho" + System.lineSeparator() + 
                                   "Jane Smith" + System.lineSeparator() + 
                                   "...";
                bulkNamesArea.setPromptText(namePrompt);
            }
            if (bulkIdsArea != null) {
                String idPrompt = "D123456A" + System.lineSeparator() + 
                                 "B987654C" + System.lineSeparator() + 
                                 "...";
                bulkIdsArea.setPromptText(idPrompt);
            }
        });

        // 设置 Single Generate 表格列
        if (singleNameColumn != null) singleNameColumn.setCellValueFactory(new PropertyValueFactory<>("name"));
        if (singleQuantityColumn != null) singleQuantityColumn.setCellValueFactory(new PropertyValueFactory<>("quantity"));
        if (singlePriceColumn != null) singlePriceColumn.setCellValueFactory(new PropertyValueFactory<>("unitPrice"));
        if (singleTotalColumn != null) singleTotalColumn.setCellValueFactory(new PropertyValueFactory<>("total"));

        // 格式化 Single Generate 数字列
        if (singlePriceColumn != null) {
            singlePriceColumn.setCellFactory(col -> new TableCell<InvoiceItem, Double>() {
                @Override
                protected void updateItem(Double item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(String.format("RM%.2f", item));
                    }
                }
            });
        }

        if (singleTotalColumn != null) {
            singleTotalColumn.setCellFactory(col -> new TableCell<InvoiceItem, Double>() {
                @Override
                protected void updateItem(Double item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(String.format("RM%.2f", item));
                    }
                }
            });
        }

        if (singleItemsTable != null) {
            singleItemsTable.setItems(items);
        }

        // 设置 Bulk Generate 表格列
        if (bulkNameColumn2 != null) bulkNameColumn2.setCellValueFactory(new PropertyValueFactory<>("name"));
        if (bulkQuantityColumn != null) bulkQuantityColumn.setCellValueFactory(new PropertyValueFactory<>("quantity"));
        if (bulkPriceColumn != null) bulkPriceColumn.setCellValueFactory(new PropertyValueFactory<>("unitPrice"));
        if (bulkTotalColumn != null) bulkTotalColumn.setCellValueFactory(new PropertyValueFactory<>("total"));

        // 格式化 Bulk Generate 数字列
        if (bulkPriceColumn != null) {
            bulkPriceColumn.setCellFactory(col -> new TableCell<InvoiceItem, Double>() {
                @Override
                protected void updateItem(Double item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(String.format("RM%.2f", item));
                    }
                }
            });
        }

        if (bulkTotalColumn != null) {
            bulkTotalColumn.setCellFactory(col -> new TableCell<InvoiceItem, Double>() {
                @Override
                protected void updateItem(Double item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || item == null) {
                        setText(null);
                    } else {
                        setText(String.format("RM%.2f", item));
                    }
                }
            });
        }

        if (bulkItemsTable != null) {
            bulkItemsTable.setItems(items);
        }

        updateTotals();

        // Initialize saved items list for Sales Items page
        if (savedItemsContainer != null) {
            loadSavedItems();  // 从文件加载保存的商品
            refreshSavedItemsList();
        }

        // Initialize bulk customer count
        updateBulkCount();

        // attempt to load saved defaults for seller and counter
        try {
            loadDefaults();
        } catch (Exception e) {
            // ignore
        }

        // init bulk table
        if (bulkTable != null && bulkNameColumn != null && bulkIdColumn != null && bulkEmailColumn != null) {
            bulkNameColumn.setCellValueFactory(new PropertyValueFactory<>("name"));
            bulkIdColumn.setCellValueFactory(new PropertyValueFactory<>("id"));
            bulkEmailColumn.setCellValueFactory(new PropertyValueFactory<>("email"));
            bulkTable.setItems(bulkList);
            
            // Setup actions column with Edit and Delete buttons
            if (bulkActionsColumn != null) {
                bulkActionsColumn.setCellFactory(param -> new TableCell<BulkBuyer, Void>() {
                    private final Button editBtn = new Button("Edit");
                    private final Button deleteBtn = new Button("Delete");
                    private final HBox pane = new HBox(5, editBtn, deleteBtn);

                    {
                        // Set minimum width for buttons to ensure they display fully
                        editBtn.setMinWidth(55);
                        editBtn.setPrefWidth(55);
                        deleteBtn.setMinWidth(60);
                        deleteBtn.setPrefWidth(60);
                        
                        editBtn.getStyleClass().add("btn-secondary-sm");
                        deleteBtn.getStyleClass().add("btn-danger-sm");
                        pane.setAlignment(Pos.CENTER);
                        
                        editBtn.setOnAction(event -> {
                            BulkBuyer buyer = getTableView().getItems().get(getIndex());
                            handleEditBulkCustomer(buyer);
                        });
                        
                        deleteBtn.setOnAction(event -> {
                            BulkBuyer buyer = getTableView().getItems().get(getIndex());
                            handleDeleteBulkCustomer(buyer);
                        });
                    }

                    @Override
                    protected void updateItem(Void item, boolean empty) {
                        super.updateItem(item, empty);
                        setGraphic(empty ? null : pane);
                    }
                });
            }
        }
    }

    /**
     * Edit a single customer in the bulk list
     */
    private void handleEditBulkCustomer(BulkBuyer buyer) {
        // Create dialog for editing
        Dialog<BulkBuyer> dialog = new Dialog<>();
        dialog.setTitle("Edit Customer");
        dialog.setHeaderText("Edit customer information");

        ButtonType saveButtonType = new ButtonType("Save", ButtonBar.ButtonData.OK_DONE);
        dialog.getDialogPane().getButtonTypes().addAll(saveButtonType, ButtonType.CANCEL);

        // Create form
        VBox content = new VBox(10);
        content.setStyle("-fx-padding: 20;");

        TextField nameField = new TextField(buyer.getName());
        nameField.setPromptText("Name");
        nameField.setPrefWidth(300);

        TextField idField = new TextField(buyer.getId());
        idField.setPromptText("ID");
        idField.setPrefWidth(300);

        TextField emailField = new TextField(buyer.getEmail());
        emailField.setPromptText("Email");
        emailField.setPrefWidth(300);

        content.getChildren().addAll(
            new Label("Name:"), nameField,
            new Label("ID:"), idField,
            new Label("Email:"), emailField
        );

        dialog.getDialogPane().setContent(content);

        // Convert result
        dialog.setResultConverter(dialogButton -> {
            if (dialogButton == saveButtonType) {
                String name = nameField.getText().trim();
                String id = idField.getText().trim();
                String email = emailField.getText().trim();
                
                if (name.isEmpty() && id.isEmpty()) {
                    showAlert("Error", "Please enter at least name or ID", Alert.AlertType.ERROR);
                    return null;
                }
                
                // 如果 email 为空，自动生成
                if (email.isEmpty() && !id.isEmpty()) {
                    email = id + "@sc.edu.my";
                }
                
                return new BulkBuyer(name, id, email);
            }
            return null;
        });

        // Show dialog and update
        dialog.showAndWait().ifPresent(updatedBuyer -> {
            int index = bulkList.indexOf(buyer);
            if (index >= 0) {
                bulkList.set(index, updatedBuyer);
                updateBulkCount();
                showAlert("Success", "Customer updated successfully", Alert.AlertType.INFORMATION);
            }
        });
    }

    /**
     * Delete a single customer from the bulk list
     */
    private void handleDeleteBulkCustomer(BulkBuyer buyer) {
        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Confirm Delete");
        confirm.setHeaderText("Delete customer?");
        confirm.setContentText("Delete: " + buyer.getName() + " (" + buyer.getId() + ")");

        confirm.showAndWait().ifPresent(response -> {
            if (response == ButtonType.OK) {
                bulkList.remove(buyer);
                updateBulkCount();
                showAlert("Success", "Customer deleted", Alert.AlertType.INFORMATION);
            }
        });
    }

    /**
     * Clear the bulk buyers list
     */
    @FXML
    private void handleClearBulkList() {
        if (bulkList.isEmpty()) {
            showAlert("Info", "The customer list is already empty", Alert.AlertType.INFORMATION);
            return;
        }

        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Confirm Clear");
        confirm.setHeaderText("Clear all customers?");
        confirm.setContentText("This will remove all " + bulkList.size() + " customers from the list.");

        confirm.showAndWait().ifPresent(response -> {
            if (response == ButtonType.OK) {
                bulkList.clear();
                if (bulkNameField != null) bulkNameField.clear();
                if (bulkIdField != null) bulkIdField.clear();
                if (bulkEmailField != null) bulkEmailField.clear();
                updateBulkCount();
                showAlert("Success", "Customer list cleared", Alert.AlertType.INFORMATION);
            }
        });
    }

    /**
     * Bulk-generate receipts: expects the current items to be the product(s) that each buyer bought.
     * Each non-empty line in the bulkBuyersArea represents one buyer. Lines may be plain name or a CSV:
     * name,address,id,phone,email
     */
    @FXML
    private void handleBulkGenerate() {
        if (items.isEmpty()) {
            showAlert("Error", "Please add at least one item before bulk-generating receipts", Alert.AlertType.ERROR);
            return;
        }

        if (bulkList == null || bulkList.isEmpty()) {
            showAlert("Error", "Please add at least one buyer to the Bulk Buyers list", Alert.AlertType.ERROR);
            return;
        }

        DirectoryChooser chooser = new DirectoryChooser();
        chooser.setTitle("Select output folder for bulk PDFs");
        // Use bulkItemsTable for window reference (or singleItemsTable if bulk is null)
        TableView<?> tableForWindow = bulkItemsTable != null ? bulkItemsTable : singleItemsTable;
        File outDir = chooser.showDialog(tableForWindow != null ? tableForWindow.getScene().getWindow() : null);
        if (outDir == null) {
            return; // user cancelled
        }

        int success = 0;
        int failed = 0;
        ArrayList<String> failedLines = new ArrayList<>();

        for (int i = 0; i < bulkList.size(); i++) {
            BulkBuyer b = bulkList.get(i);
            String name = b.getName() == null ? "" : b.getName().trim();
            String id = b.getId() == null ? "" : b.getId().trim();
            String email = b.getEmail() == null ? "" : b.getEmail().trim();

            try {
                Invoice invoice = new Invoice();
                String generatedNumber = generateInvoiceNumber();
                invoice.setInvoiceNumber(generatedNumber);
                // Use current date if invoiceDatePicker doesn't exist
                invoice.setInvoiceDate(invoiceDatePicker != null ? invoiceDatePicker.getValue() : LocalDate.now());
                invoice.setNotes(notesArea != null ? notesArea.getText() : "");

                // seller from current form
                Company seller = new Company(
                        sellerNameField != null ? sellerNameField.getText() : "",
                        sellerAddressField != null ? sellerAddressField.getText() : "",
                        "", // Tax ID not in new UI
                        sellerPhoneField != null ? sellerPhoneField.getText() : "",
                        sellerEmailField != null ? sellerEmailField.getText() : ""
                );
                invoice.setSeller(seller);

                // If email is empty but id is provided, use id@sc.edu.my as the fallback email for bulk generation
                String effectiveEmail = email;
                if ((effectiveEmail == null || effectiveEmail.trim().isEmpty()) && id != null && !id.trim().isEmpty()) {
                    effectiveEmail = id.trim() + "@sc.edu.my";
                }
                Company buyer = new Company(name, "", id, "", effectiveEmail);
                invoice.setBuyer(buyer);

                invoice.setItems(new ArrayList<>(items));

                // paid handling
                double grandTotal = invoice.getGrandTotal();
                if (paidCheckBox != null && paidCheckBox.isSelected()) {
                    invoice.setPaidAmount(grandTotal);
                } else {
                    invoice.setPaidAmount(0.0);
                }

                // build output file path: prefer name-id.pdf
                String sanitized = sanitizeFileName(name);
                String idSan = sanitizeFileName(id);
                String filename;
                if (id != null && !id.trim().isEmpty()) {
                    // use underscore between name and id for bulk filenames as requested
                    filename = sanitized + "_" + idSan + ".pdf";
                } else if (sanitized != null && !sanitized.trim().isEmpty()) {
                    filename = sanitized + ".pdf";
                } else {
                    filename = invoice.getInvoiceNumber() + ".pdf";
                }
                File outFile = new File(outDir, filename);

                pdfGenerator.generatePDF(invoice, outFile.getAbsolutePath());
                invoiceService.saveInvoice(invoice);
                success++;
            } catch (Exception e) {
                failed++;
                failedLines.add(name + " (" + id + ")");
                e.printStackTrace();
            }
        }

        String msg = String.format("Bulk generation finished. Success: %d, Failed: %d", success, failed);
        if (!failedLines.isEmpty()) {
            msg += "\nFailed lines:\n" + String.join("\n", failedLines);
        }
        showAlert("Bulk Generate", msg, Alert.AlertType.INFORMATION);
    }

    // (old simple generateInvoiceNumber removed — replaced by persisted-counter version below)

    /**
     * 添加商品到库存
     */
    @FXML
    private void handleAddItem() {
        try {
            String name = itemNameField.getText().trim();
            double price = Double.parseDouble(itemPriceField.getText());
            double taxRate = Double.parseDouble(itemTaxRateField.getText());

            if (name.isEmpty()) {
                showAlert("Error", "Please enter the item name", Alert.AlertType.ERROR);
                return;
            }

            // 默认数量设置为1
            InvoiceItem item = new InvoiceItem(name, 1, price, taxRate);
            savedItems.add(item);

            // 清空输入框
            itemNameField.clear();
            itemPriceField.clear();
            itemTaxRateField.setText("0.0");

            // 刷新显示
            refreshSavedItemsList();
            
            // 保存到文件
            saveSavedItems();
            
            showAlert("Success", "Item added successfully!", Alert.AlertType.INFORMATION);
        } catch (NumberFormatException e) {
            showAlert("Error", "Please enter valid numbers", Alert.AlertType.ERROR);
        }
    }
    
    /**
     * 刷新商品列表显示
     */
    private void refreshSavedItemsList() {
        if (savedItemsContainer == null) return;
        
        savedItemsContainer.getChildren().clear();
        
        for (InvoiceItem item : savedItems) {
            HBox itemCard = new HBox(15);
            itemCard.setAlignment(Pos.CENTER_LEFT);
            itemCard.getStyleClass().add("item-card");
            
            // 左侧信息
            VBox info = new VBox(4);
            HBox.setHgrow(info, javafx.scene.layout.Priority.ALWAYS);
            
            Label nameLabel = new Label(item.getName());
            nameLabel.getStyleClass().add("item-title");
            
            Label detailsLabel = new Label(String.format("RM %.2f", item.getUnitPrice()));
            detailsLabel.getStyleClass().add("item-subtitle");
            
            info.getChildren().addAll(nameLabel, detailsLabel);
            
            // 按钮
            Button editBtn = new Button("Edit");
            editBtn.getStyleClass().add("btn-secondary-sm");
            editBtn.setOnAction(e -> editItem(item));
            
            Button deleteBtn = new Button("Delete");
            deleteBtn.getStyleClass().add("btn-danger-sm");
            deleteBtn.setOnAction(e -> deleteItem(item));
            
            itemCard.getChildren().addAll(info, editBtn, deleteBtn);
            savedItemsContainer.getChildren().add(itemCard);
        }
    }
    
    /**
     * 编辑商品
     */
    private void editItem(InvoiceItem item) {
        // Create dialog for editing
        Dialog<InvoiceItem> dialog = new Dialog<>();
        dialog.setTitle("Edit Item");
        dialog.setHeaderText("Edit item information");

        ButtonType saveButtonType = new ButtonType("Save", ButtonBar.ButtonData.OK_DONE);
        dialog.getDialogPane().getButtonTypes().addAll(saveButtonType, ButtonType.CANCEL);

        // Create form
        javafx.scene.layout.GridPane grid = new javafx.scene.layout.GridPane();
        grid.setHgap(10);
        grid.setVgap(10);
        grid.setStyle("-fx-padding: 20;");

        TextField nameField = new TextField(item.getName());
        nameField.setPromptText("Product Name");
        nameField.setPrefWidth(300);

        TextField priceField = new TextField(String.valueOf(item.getUnitPrice()));
        priceField.setPromptText("Price");
        priceField.setPrefWidth(300);

        TextField taxRateField = new TextField(String.valueOf(item.getTaxRate()));
        taxRateField.setPromptText("Tax Rate (%)");
        taxRateField.setPrefWidth(300);

        grid.add(new Label("Product Name:"), 0, 0);
        grid.add(nameField, 1, 0);
        grid.add(new Label("Price (RM):"), 0, 1);
        grid.add(priceField, 1, 1);
        grid.add(new Label("Tax Rate (%):"), 0, 2);
        grid.add(taxRateField, 1, 2);

        dialog.getDialogPane().setContent(grid);

        // Convert result
        dialog.setResultConverter(dialogButton -> {
            if (dialogButton == saveButtonType) {
                try {
                    String name = nameField.getText().trim();
                    double price = Double.parseDouble(priceField.getText().trim());
                    double taxRate = Double.parseDouble(taxRateField.getText().trim());
                    
                    if (name.isEmpty()) {
                        showAlert("Error", "Please enter the product name", Alert.AlertType.ERROR);
                        return null;
                    }
                    
                    if (price < 0 || taxRate < 0) {
                        showAlert("Error", "Please enter valid positive values", Alert.AlertType.ERROR);
                        return null;
                    }
                    
                    // 默认数量设为1
                    return new InvoiceItem(name, 1, price, taxRate);
                } catch (NumberFormatException e) {
                    showAlert("Error", "Please enter valid numbers for price and tax rate", Alert.AlertType.ERROR);
                    return null;
                }
            }
            return null;
        });

        // Show dialog and update
        dialog.showAndWait().ifPresent(updatedItem -> {
            int index = savedItems.indexOf(item);
            if (index >= 0) {
                String oldName = item.getName();
                savedItems.set(index, updatedItem);
                
                // 同时更新发票列表中的同名商品的价格和税率
                for (InvoiceItem invoiceItem : items) {
                    if (invoiceItem.getName().equals(oldName)) {
                        invoiceItem.setName(updatedItem.getName());
                        invoiceItem.setUnitPrice(updatedItem.getUnitPrice());
                        invoiceItem.setTaxRate(updatedItem.getTaxRate());
                    }
                }
                
                // 刷新表格显示
                if (singleItemsTable != null) {
                    singleItemsTable.refresh();
                }
                if (bulkItemsTable != null) {
                    bulkItemsTable.refresh();
                }
                updateTotals();
                
                refreshSavedItemsList();
                saveSavedItems();
                showAlert("Success", "Item updated successfully", Alert.AlertType.INFORMATION);
            }
        });
    }
    
    /**
     * 删除商品
     */
    private void deleteItem(InvoiceItem item) {
        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Confirm Delete");
        confirm.setHeaderText("Delete Item");
        confirm.setContentText("Are you sure you want to delete " + item.getName() + "?");
        
        confirm.showAndWait().ifPresent(response -> {
            if (response == ButtonType.OK) {
                savedItems.remove(item);
                
                // 同时从当前发票列表中移除同名商品
                items.removeIf(invoiceItem -> invoiceItem.getName().equals(item.getName()));
                
                // 刷新表格显示
                if (singleItemsTable != null) {
                    singleItemsTable.refresh();
                }
                if (bulkItemsTable != null) {
                    bulkItemsTable.refresh();
                }
                updateTotals();
                
                refreshSavedItemsList();
                saveSavedItems();
            }
        });
    }

    /**
     * Add a buyer row into the bulk list using the small input fields
     */
    @FXML
    private void handleAddBulkRow() {
        String name = bulkNameField.getText().trim();
        String id = bulkIdField.getText().trim();
        String email = bulkEmailField.getText().trim();
        if (name.isEmpty() && id.isEmpty() && email.isEmpty()) {
            showAlert("Error", "Please enter at least one field for the buyer", Alert.AlertType.ERROR);
            return;
        }
        bulkList.add(new BulkBuyer(name, id, email));
        bulkNameField.clear();
        bulkIdField.clear();
        bulkEmailField.clear();
    }

    @FXML
    private void handleRemoveBulkRow() {
        BulkBuyer sel = bulkTable.getSelectionModel().getSelectedItem();
        if (sel != null) {
            bulkList.remove(sel);
        } else {
            showAlert("Warning", "Please select a row to remove", Alert.AlertType.WARNING);
        }
    }

    /**
     * 删除选中的商品
     */
    @FXML
    private void handleRemoveItem() {
        // Try to get selected item from either table
        InvoiceItem selected = null;
        if (singleItemsTable != null) {
            selected = singleItemsTable.getSelectionModel().getSelectedItem();
        }
        if (selected == null && bulkItemsTable != null) {
            selected = bulkItemsTable.getSelectionModel().getSelectedItem();
        }
        
        if (selected != null) {
            items.remove(selected);
            updateTotals();
        } else {
            showAlert("Warning", "Please select an item to remove", Alert.AlertType.WARNING);
        }
    }
    /**
     * 添加商品到发票（从库存中选择）
     */
    @FXML
    private void handleAddItemToInvoice() {
        if (savedItems.isEmpty()) {
            showAlert("No Items", "Please add items to Sales Items first before adding them to the invoice.", Alert.AlertType.WARNING);
            return;
        }

        // 创建对话框让用户选择商品和数量
        Dialog<InvoiceItem> dialog = new Dialog<>();
        dialog.setTitle("Add Item to Invoice");
        dialog.setHeaderText("Select item from inventory and specify quantity");

        // 设置按钮
        ButtonType addButtonType = new ButtonType("Add", ButtonBar.ButtonData.OK_DONE);
        dialog.getDialogPane().getButtonTypes().addAll(addButtonType, ButtonType.CANCEL);

        // 创建表单
        VBox content = new VBox(10);
        content.setStyle("-fx-padding: 20;");

        Label itemLabel = new Label("Select Item:");
        ComboBox<InvoiceItem> itemComboBox = new ComboBox<>(savedItems);
        itemComboBox.setPromptText("Choose an item");
        itemComboBox.setPrefWidth(300);
        
        // 自定义ComboBox显示
        itemComboBox.setCellFactory(param -> new ListCell<InvoiceItem>() {
            @Override
            protected void updateItem(InvoiceItem item, boolean empty) {
                super.updateItem(item, empty);
                if (empty || item == null) {
                    setText(null);
                } else {
                    setText(String.format("%s - RM %.2f", item.getName(), item.getUnitPrice()));
                }
            }
        });
        itemComboBox.setButtonCell(new ListCell<InvoiceItem>() {
            @Override
            protected void updateItem(InvoiceItem item, boolean empty) {
                super.updateItem(item, empty);
                if (empty || item == null) {
                    setText(null);
                } else {
                    setText(String.format("%s - RM %.2f", item.getName(), item.getUnitPrice()));
                }
            }
        });

        Label quantityLabel = new Label("Quantity:");
        TextField quantityField = new TextField("1");
        quantityField.setPrefWidth(300);

        content.getChildren().addAll(itemLabel, itemComboBox, quantityLabel, quantityField);
        dialog.getDialogPane().setContent(content);

        // 转换结果
        dialog.setResultConverter(dialogButton -> {
            if (dialogButton == addButtonType) {
                try {
                    InvoiceItem selectedItem = itemComboBox.getValue();
                    if (selectedItem == null) {
                        showAlert("Error", "Please select an item", Alert.AlertType.ERROR);
                        return null;
                    }
                    
                    int quantity = Integer.parseInt(quantityField.getText());
                    if (quantity <= 0) {
                        showAlert("Error", "Quantity must be greater than 0", Alert.AlertType.ERROR);
                        return null;
                    }

                    // 创建新的InvoiceItem实例（基于选中的商品）
                    return new InvoiceItem(
                        selectedItem.getName(),
                        quantity,
                        selectedItem.getUnitPrice(),
                        selectedItem.getTaxRate()
                    );
                } catch (NumberFormatException e) {
                    showAlert("Error", "Please enter a valid quantity", Alert.AlertType.ERROR);
                    return null;
                }
            }
            return null;
        });

        // 显示对话框并处理结果
        dialog.showAndWait().ifPresent(newItem -> {
            items.add(newItem);
            // Refresh both tables
            if (singleItemsTable != null) {
                singleItemsTable.refresh();
            }
            if (bulkItemsTable != null) {
                bulkItemsTable.refresh();
            }
            updateTotals();
        });
    }

    /**
     * 更新总计
     */
    private void updateTotals() {
        double total = items.stream().mapToDouble(InvoiceItem::getTotal).sum();

        // Update both Single and Bulk labels
        if (singleTotalLabel != null) singleTotalLabel.setText(String.format("RM%.2f", total));
        if (bulkTotalLabel != null) bulkTotalLabel.setText(String.format("RM%.2f", total));
        
        // Update legacy labels if they exist
        if (subtotalLabel != null) {
            double subtotal = items.stream().mapToDouble(InvoiceItem::getSubtotal).sum();
            subtotalLabel.setText(String.format("RM%.2f", subtotal));
        }
        if (taxLabel != null) {
            double tax = items.stream().mapToDouble(InvoiceItem::getTaxAmount).sum();
            taxLabel.setText(String.format("RM%.2f", tax));
        }
        if (totalLabel != null) totalLabel.setText(String.format("RM%.2f", total));
    }

    /**
     * 生成PDF发票
     */
    @FXML
    private void handleGeneratePDF() {
        if (!validateForm()) {
            return;
        }

        Invoice invoice = createInvoiceFromForm();

        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Save Invoice");
        // Default filename: buyerName-buyerId.pdf if available, otherwise invoice number
        String defaultBase = invoice.getInvoiceNumber();
        if (invoice.getBuyer() != null) {
            String bName = invoice.getBuyer().getName();
            String bId = invoice.getBuyer().getTaxId();
            if (bName != null && !bName.trim().isEmpty()) {
                defaultBase = sanitizeFileName(bName.trim());
                if (bId != null && !bId.trim().isEmpty()) {
                    defaultBase += "-" + sanitizeFileName(bId.trim());
                }
            }
        }
        fileChooser.setInitialFileName(defaultBase + ".pdf");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("PDF Files", "*.pdf")
        );

        // Use singleItemsTable for window reference (or bulkItemsTable if single is null)
        TableView<?> tableForWindow = singleItemsTable != null ? singleItemsTable : bulkItemsTable;
        File file = fileChooser.showSaveDialog(tableForWindow != null ? tableForWindow.getScene().getWindow() : null);
        if (file != null) {
            try {
                pdfGenerator.generatePDF(invoice, file.getAbsolutePath());
                invoiceService.saveInvoice(invoice);
                showAlert("Success", "Invoice generated and saved to:\n" + file.getAbsolutePath(), Alert.AlertType.INFORMATION);

                // After generating, offer to send via Outlook
                askToSendViaOutlook(invoice, file.getAbsolutePath());

            } catch (Exception e) {
                showAlert("Error", "Failed to generate PDF: " + e.getMessage(), Alert.AlertType.ERROR);
                e.printStackTrace();
            }
        }
    }

    /**
     * Prompt the user whether to send the generated PDF via Outlook.
     * Offers two modes: Open compose window (review) or Send now (automatic).
     */
    private void askToSendViaOutlook(Invoice invoice, String attachmentPath) {
        // Determine default recipient (buyer email)
        String defaultTo = "";
        if (invoice.getBuyer() != null && invoice.getBuyer().getEmail() != null) {
            defaultTo = invoice.getBuyer().getEmail();
        }

        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Send via Outlook");
        confirm.setHeaderText("Do you want to send this invoice via Outlook?");
        confirm.setContentText("Choose 'Send Now' to programmatically send, or 'Open in Outlook' to review before sending.");

        ButtonType sendNow = new ButtonType("Send Now");
        ButtonType openCompose = new ButtonType("Open in Outlook");
        ButtonType cancel = new ButtonType("Cancel", ButtonBar.ButtonData.CANCEL_CLOSE);

        confirm.getButtonTypes().setAll(sendNow, openCompose, cancel);
        ButtonType result = confirm.showAndWait().orElse(cancel);

        if (result == cancel) return;

        // Get recipient email (use buyer email if present, otherwise ask)
        String to = defaultTo;
        if (to == null || to.trim().isEmpty()) {
            TextInputDialog input = new TextInputDialog();
            input.setTitle("Recipient Email");
            input.setHeaderText("No recipient email found");
            input.setContentText("Enter recipient email:");
            to = input.showAndWait().orElse("");
            if (to.trim().isEmpty()) {
                showAlert("Info", "No recipient provided. Skipping email.", Alert.AlertType.INFORMATION);
                return;
            }
        }

        String subject = "Receipt " + invoice.getInvoiceNumber();
        String body = "Please find attached the receipt " + invoice.getInvoiceNumber() + "\nTotal: RM" + String.format("%.2f", invoice.getGrandTotal()) + "\n\n" + (invoice.getNotes() == null ? "" : invoice.getNotes());

        boolean autoSend = (result == sendNow);
        try {
            boolean ok = sendViaOutlookPowerShell(to, subject, body, attachmentPath, autoSend);
            if (ok) {
                showAlert("Info", (autoSend ? "Email sent via Outlook." : "Opened in Outlook for review."), Alert.AlertType.INFORMATION);
            } else {
                showAlert("Error", "Failed to invoke Outlook. Make sure Outlook is installed and configured.", Alert.AlertType.ERROR);
            }
        } catch (Exception e) {
            showAlert("Error", "Error while sending via Outlook: " + e.getMessage(), Alert.AlertType.ERROR);
            e.printStackTrace();
        }
    }

    /**
     * Use PowerShell to automate Outlook via COM. This avoids adding native JNI libraries.
     * The script will either Display() the message (open compose window) or Send() it directly.
     */
    private boolean sendViaOutlookPowerShell(String to, String subject, String body, String attachmentPath, boolean sendNow) throws IOException, InterruptedException {
        // Only supported on Windows with Outlook installed
        String os = System.getProperty("os.name").toLowerCase();
        if (!os.contains("win")) {
            return false;
        }

        // Build PowerShell script content
        String ps = "try {\n" +
                "  $to = \"" + escapeForPowerShell(to) + "\";\n" +
                "  $subject = \"" + escapeForPowerShell(subject) + "\";\n" +
                "  $body = \"" + escapeForPowerShell(body) + "\";\n" +
                "  $attachment = \"" + escapeForPowerShell(attachmentPath) + "\";\n" +
                "  $ol = New-Object -ComObject Outlook.Application;\n" +
                "  $mail = $ol.CreateItem(0);\n" +
                "  $mail.To = $to;\n" +
                "  $mail.Subject = $subject;\n" +
                "  $mail.Body = $body;\n" +
                "  if (Test-Path $attachment) { $mail.Attachments.Add($attachment) };\n" +
                (sendNow ? "  $mail.Send();\n" : "  $mail.Display();\n") +
                "  exit 0;\n" +
                "} catch {\n" +
                "  Write-Error $_.Exception.Message;\n" +
                "  exit 1;\n" +
                "}";

        // write to temp file
        File tmp = File.createTempFile("send_outlook_", ".ps1");
        java.nio.file.Files.writeString(tmp.toPath(), ps, java.nio.charset.StandardCharsets.UTF_8);

        // run powershell
        ProcessBuilder pb = new ProcessBuilder("powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tmp.getAbsolutePath());
        pb.redirectErrorStream(true);
        Process p = pb.start();
    // capture output (not shown to user) for debug (read and ignore)
    p.getInputStream().readAllBytes();
    int code = p.waitFor();

        // cleanup
        try { tmp.delete(); } catch (Exception ignored) {}

        return code == 0;
    }

    private String escapeForPowerShell(String s) {
        if (s == null) return "";
        return s.replace("`", "``").replace("\"", "`\"").replace("\r", "").replace("\n", "\n");
    }

    /**
     * 验证表单
     */
    private boolean validateForm() {
        if (sellerNameField.getText().trim().isEmpty()) {
            showAlert("Error", "Please fill in the seller company name", Alert.AlertType.ERROR);
            return false;
        }
        if (buyerNameField.getText().trim().isEmpty()) {
            showAlert("Error", "Please fill in the buyer name", Alert.AlertType.ERROR);
            return false;
        }
        if (items.isEmpty()) {
            showAlert("Error", "Please add at least one item", Alert.AlertType.ERROR);
            return false;
        }
        return true;
    }

    /**
     * 从表单创建发票对象
     */
    private Invoice createInvoiceFromForm() {
        Invoice invoice = new Invoice();
        // Generate invoice number at the time of creating the invoice to ensure it's fresh
        String generatedNumber = generateInvoiceNumber();
        invoice.setInvoiceNumber(generatedNumber);
        // Note: invoiceNumberField removed from new UI design, no need to update it
        
        // Use current date if invoiceDatePicker doesn't exist
        invoice.setInvoiceDate(invoiceDatePicker != null ? invoiceDatePicker.getValue() : LocalDate.now());
        invoice.setNotes(notesArea != null ? notesArea.getText() : "");

        Company seller = new Company(
            sellerNameField != null ? sellerNameField.getText() : "",
            sellerAddressField != null ? sellerAddressField.getText() : "",
            "", // Tax ID not in new UI
            sellerPhoneField != null ? sellerPhoneField.getText() : "",
            sellerEmailField != null ? sellerEmailField.getText() : ""
        );
        invoice.setSeller(seller);

        // Auto-generate email if empty: id + @sc.edu.my
        String buyerEmail = buyerEmailField != null ? buyerEmailField.getText().trim() : "";
        if (buyerEmail.isEmpty()) {
            String buyerId = buyerTaxIdField != null ? buyerTaxIdField.getText().trim() : "";
            if (!buyerId.isEmpty()) {
                buyerEmail = buyerId + "@sc.edu.my";
            }
        }
        
        Company buyer = new Company(
            buyerNameField != null ? buyerNameField.getText() : "",
            "", // address not in new UI
            buyerTaxIdField != null ? buyerTaxIdField.getText() : "",
            "", // phone not in new UI
            buyerEmail
        );
        invoice.setBuyer(buyer);

        invoice.setItems(new ArrayList<>(items));

        // If the "Mark as Paid" checkbox is selected, and no explicit paid amount is provided,
        // treat the invoice as fully paid by setting paidAmount to the grand total.
        double grandTotal = invoice.getGrandTotal();
        if (paidCheckBox != null && paidCheckBox.isSelected()) {
            invoice.setPaidAmount(grandTotal);
        } else {
            // keep default 0.0 unless user later adds a paid amount feature
            invoice.setPaidAmount(0.0);
        }

        return invoice;
    }

    /**
     * Generate invoice number with persisted counter: INV-yyyymmdd-HHmm-cccc
     * cccc is 4-digit zero-padded counter starting at 0001 and incremented per invoice.
     */
    private synchronized String generateInvoiceNumber() {
        String dt = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmm"));
        int counterToUse = getAndIncrementInvoiceCounter();
        return "INV-" + dt + "-" + String.format("%04d", counterToUse);
    }

    /**
     * Return current invoiceCounter (next to use) and advance it, persisting the next value.
     */
    private synchronized int getAndIncrementInvoiceCounter() {
        int use = invoiceCounter; // current next-to-use
        // advance for next time
        invoiceCounter = (invoiceCounter % 9999) + 1;
        // persist the "next to use" value
        try {
            Properties p = new Properties();
            if (defaultsFile.exists()) {
                try (FileInputStream fis = new FileInputStream(defaultsFile)) {
                    p.load(fis);
                }
            }
            p.setProperty("invoice.counter", String.valueOf(invoiceCounter));
            try (FileOutputStream fos = new FileOutputStream(defaultsFile)) {
                p.store(fos, "Invoice Generator Defaults");
            }
        } catch (IOException e) {
            // best-effort persistence; ignore failures but print stack for debugging
            e.printStackTrace();
        }
        return use;
    }

    /**
     * Save current seller fields as defaults in a properties file in the user's home directory.
     */
    @FXML
    private void handleSaveDefaults() {
        Properties p = new Properties();
        p.setProperty("seller.name", sellerNameField.getText() == null ? "" : sellerNameField.getText());
        p.setProperty("seller.address", sellerAddressField.getText() == null ? "" : sellerAddressField.getText());
        p.setProperty("seller.taxId", sellerTaxIdField.getText() == null ? "" : sellerTaxIdField.getText());
        p.setProperty("seller.phone", sellerPhoneField.getText() == null ? "" : sellerPhoneField.getText());
        p.setProperty("seller.email", sellerEmailField.getText() == null ? "" : sellerEmailField.getText());
        p.setProperty("invoice.counter", String.valueOf(invoiceCounter));

        try (FileOutputStream fos = new FileOutputStream(defaultsFile)) {
            p.store(fos, "Invoice Generator Defaults");
            showAlert("Success", "Defaults saved to: " + defaultsFile.getAbsolutePath(), Alert.AlertType.INFORMATION);
        } catch (IOException e) {
            showAlert("Error", "Failed to save defaults: " + e.getMessage(), Alert.AlertType.ERROR);
            e.printStackTrace();
        }
    }

    /**
     * Load default seller values if defaults file exists.
     */
    @FXML
    private void handleLoadDefaults() {
        try {
            loadDefaults();
            showAlert("Success", "Defaults loaded", Alert.AlertType.INFORMATION);
        } catch (Exception e) {
            showAlert("Error", "Failed to load defaults: " + e.getMessage(), Alert.AlertType.ERROR);
            e.printStackTrace();
        }
    }

    /**
     * Save seller information from Seller Info page.
     */
    @FXML
    private void handleSaveSellerInfo() {
        // Validate that at least name is filled
        if (sellerNameField.getText() == null || sellerNameField.getText().trim().isEmpty()) {
            showAlert("Validation Error", "Organization name is required", Alert.AlertType.WARNING);
            return;
        }

        Properties p = new Properties();
        // Load existing properties to preserve invoice counter
        if (defaultsFile.exists()) {
            try (FileInputStream fis = new FileInputStream(defaultsFile)) {
                p.load(fis);
            } catch (IOException e) {
                // Ignore, we'll create new file
            }
        }

        // Update seller properties
        p.setProperty("seller.name", sellerNameField.getText());
        p.setProperty("seller.email", sellerEmailField.getText() == null ? "" : sellerEmailField.getText());
        
        // Check if logo exists in resources and save flag
        File logoFile = new File("src/main/resources/img/logo.png");
        if (logoFile.exists()) {
            p.setProperty("seller.hasLogo", "true");
            logoFilePath = logoFile.getAbsolutePath();
        } else {
            p.setProperty("seller.hasLogo", "false");
        }
        
        // Save phone and address if fields exist (for backward compatibility)
        if (sellerPhoneField != null) {
            p.setProperty("seller.phone", sellerPhoneField.getText() == null ? "" : sellerPhoneField.getText());
        }
        if (sellerAddressField != null) {
            p.setProperty("seller.address", sellerAddressField.getText() == null ? "" : sellerAddressField.getText());
        }
        
        // Save taxId if field exists
        if (sellerTaxIdField != null) {
            p.setProperty("seller.taxId", sellerTaxIdField.getText() == null ? "" : sellerTaxIdField.getText());
        }

        try (FileOutputStream fos = new FileOutputStream(defaultsFile)) {
            p.store(fos, "Invoice Generator Defaults");
            
            // Update receipt preview after saving
            updateReceiptPreview();
            
            showAlert("Success", "Seller information saved successfully", Alert.AlertType.INFORMATION);
        } catch (IOException e) {
            showAlert("Error", "Failed to save seller information: " + e.getMessage(), Alert.AlertType.ERROR);
            e.printStackTrace();
        }
    }

    /**
     * Cancel seller info changes and reload from saved defaults.
     */
    @FXML
    private void handleCancelSellerInfo() {
        try {
            loadDefaults();
            showAlert("Info", "Seller information restored from saved defaults", Alert.AlertType.INFORMATION);
        } catch (Exception e) {
            // If no defaults exist, just clear the fields
            sellerNameField.clear();
            sellerEmailField.clear();
            if (sellerPhoneField != null) sellerPhoneField.clear();
            if (sellerAddressField != null) sellerAddressField.clear();
            showAlert("Info", "No saved defaults found. Fields cleared.", Alert.AlertType.INFORMATION);
        }
    }

    /**
     * Handle logo file selection
     */
    @FXML
    private void handleChooseLogo() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Choose Logo Image");
        fileChooser.getExtensionFilters().addAll(
            new FileChooser.ExtensionFilter("Image Files", "*.png", "*.jpg", "*.jpeg", "*.gif")
        );
        
        File file = fileChooser.showOpenDialog(sellerNameField.getScene().getWindow());
        if (file != null) {
            try {
                // Define the target path in resources
                File targetDir = new File("src/main/resources/img");
                if (!targetDir.exists()) {
                    targetDir.mkdirs();
                }
                
                File targetFile = new File(targetDir, "logo.png");
                
                // Copy the selected file to the target location
                java.nio.file.Files.copy(
                    file.toPath(), 
                    targetFile.toPath(), 
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING
                );
                
                // Update the logo path to use the resources path
                logoFilePath = targetFile.getAbsolutePath();
                logoFileLabel.setText("logo.png (saved)");
                
                // Update logo preview
                updateLogoPreview(logoFilePath);
                
                showAlert("Success", "Logo uploaded and saved to resources/img/logo.png", Alert.AlertType.INFORMATION);
            } catch (IOException e) {
                showAlert("Error", "Failed to save logo: " + e.getMessage(), Alert.AlertType.ERROR);
                e.printStackTrace();
            }
        }
    }

    /**
     * Update logo preview in the UI
     */
    private void updateLogoPreview(String imagePath) {
        if (logoPreviewBox == null) return;
        
        try {
            logoPreviewBox.getChildren().clear();
            
            if (imagePath != null && !imagePath.isEmpty()) {
                File imgFile = new File(imagePath);
                if (imgFile.exists()) {
                    javafx.scene.image.Image image = new javafx.scene.image.Image(imgFile.toURI().toString());
                    javafx.scene.image.ImageView imageView = new javafx.scene.image.ImageView(image);
                    imageView.setPreserveRatio(true);
                    imageView.setFitHeight(100);
                    imageView.setFitWidth(200);
                    logoPreviewBox.getChildren().add(imageView);
                } else {
                    Label label = new Label("Logo file not found");
                    label.setStyle("-fx-text-fill: #9CA3AF; -fx-font-size: 12px;");
                    logoPreviewBox.getChildren().add(label);
                }
            } else {
                Label label = new Label("Logo Preview");
                label.setStyle("-fx-text-fill: #9CA3AF; -fx-font-size: 12px;");
                logoPreviewBox.getChildren().add(label);
            }
        } catch (Exception e) {
            e.printStackTrace();
            Label errorLabel = new Label("Error loading logo");
            errorLabel.setStyle("-fx-text-fill: #EF4444; -fx-font-size: 12px;");
            logoPreviewBox.getChildren().clear();
            logoPreviewBox.getChildren().add(errorLabel);
        }
    }

    /**
     * Update receipt preview - generates actual PDF and displays it
     */
    private void updateReceiptPreview() {
        if (receiptPreviewBox == null) return;
        
        receiptPreviewBox.getChildren().clear();
        
        try {
            // Create a sample invoice for preview
            Invoice sampleInvoice = new Invoice();
            sampleInvoice.setInvoiceNumber("INV-20241103-0001");
            sampleInvoice.setInvoiceDate(java.time.LocalDate.now());
            sampleInvoice.setNotes("Sample preview");
            
            // Seller info
            String orgName = sellerNameField.getText();
            if (orgName == null || orgName.trim().isEmpty()) {
                orgName = "Your Organization";
            }
            String email = sellerEmailField.getText();
            if (email == null || email.trim().isEmpty()) {
                email = "email@example.com";
            }
            Company seller = new Company(orgName, "", "", "", email);
            sampleInvoice.setSeller(seller);
            
            // Sample buyer
            Company buyer = new Company("Sample Customer", "", "A12345678", "", "customer@example.com");
            sampleInvoice.setBuyer(buyer);
            
            // Sample items
            java.util.List<InvoiceItem> sampleItems = new java.util.ArrayList<>();
            sampleItems.add(new InvoiceItem("Sample Item 1", 2, 15.00, 0.0));
            sampleItems.add(new InvoiceItem("Sample Item 2", 1, 25.00, 0.0));
            sampleInvoice.setItems(sampleItems);
            sampleInvoice.setPaidAmount(sampleInvoice.getGrandTotal());
            
            // Generate preview PDF to temp file
            File tempDir = new File(System.getProperty("java.io.tmpdir"), "invoice_preview");
            if (!tempDir.exists()) {
                tempDir.mkdirs();
            }
            File tempPdf = new File(tempDir, "preview.pdf");
            
            pdfGenerator.generatePDF(sampleInvoice, tempPdf.getAbsolutePath());
            
            // Convert PDF to image and display
            displayPdfPreview(tempPdf);
            
        } catch (Exception e) {
            e.printStackTrace();
            // Show error message in preview
            Label errorLabel = new Label("Preview unavailable\n" + e.getMessage());
            errorLabel.setStyle("-fx-text-fill: #EF4444; -fx-font-size: 11px; -fx-padding: 20;");
            errorLabel.setWrapText(true);
            errorLabel.setTextAlignment(javafx.scene.text.TextAlignment.CENTER);
            errorLabel.setAlignment(javafx.geometry.Pos.CENTER);
            receiptPreviewBox.getChildren().add(errorLabel);
        }
    }
    
    /**
     * Display PDF preview as image
     */
    private void displayPdfPreview(File pdfFile) {
        if (receiptPreviewBox == null || !pdfFile.exists()) return;
        
        try {
            // Use PDFBox to render PDF to image
            org.apache.pdfbox.pdmodel.PDDocument document = org.apache.pdfbox.pdmodel.PDDocument.load(pdfFile);
            org.apache.pdfbox.rendering.PDFRenderer pdfRenderer = new org.apache.pdfbox.rendering.PDFRenderer(document);
            
            // Render first page at 150 DPI (good quality for preview)
            java.awt.image.BufferedImage bufferedImage = pdfRenderer.renderImageWithDPI(0, 150, org.apache.pdfbox.rendering.ImageType.RGB);
            
            // Convert BufferedImage to JavaFX Image
            javafx.scene.image.WritableImage fxImage = new javafx.scene.image.WritableImage(
                bufferedImage.getWidth(), 
                bufferedImage.getHeight()
            );
            
            javafx.scene.image.PixelWriter pixelWriter = fxImage.getPixelWriter();
            for (int y = 0; y < bufferedImage.getHeight(); y++) {
                for (int x = 0; x < bufferedImage.getWidth(); x++) {
                    pixelWriter.setArgb(x, y, bufferedImage.getRGB(x, y));
                }
            }
            
            document.close();
            
            // Create ImageView with the rendered PDF
            javafx.scene.image.ImageView imageView = new javafx.scene.image.ImageView(fxImage);
            imageView.setPreserveRatio(true);
            
            // Bind image width to preview box width for responsive scaling
            // Use a slightly smaller width to account for padding
            if (receiptPreviewBox != null) {
                imageView.fitWidthProperty().bind(receiptPreviewBox.widthProperty().subtract(60));
            } else {
                imageView.setFitWidth(500);
            }
            
            // Add to ScrollPane for vertical scrolling if needed
            javafx.scene.control.ScrollPane scrollPane = new javafx.scene.control.ScrollPane(imageView);
            scrollPane.setFitToWidth(true);
            scrollPane.setStyle("-fx-background-color: transparent; -fx-background: transparent;");
            scrollPane.setVbarPolicy(javafx.scene.control.ScrollPane.ScrollBarPolicy.AS_NEEDED);
            scrollPane.setHbarPolicy(javafx.scene.control.ScrollPane.ScrollBarPolicy.NEVER);
            
            // Add open PDF button at bottom
            VBox container = new VBox(10);
            container.setAlignment(javafx.geometry.Pos.TOP_CENTER);
            
            container.getChildren().add(scrollPane);
            
            javafx.scene.control.Button openButton = new javafx.scene.control.Button("Open Full PDF");
            openButton.setStyle("-fx-background-color: #4F46E5; -fx-text-fill: white; -fx-padding: 6 12; -fx-background-radius: 6; -fx-cursor: hand; -fx-font-size: 11px;");
            openButton.setOnAction(e -> {
                try {
                    java.awt.Desktop.getDesktop().open(pdfFile);
                } catch (Exception ex) {
                    showAlert("Error", "Failed to open PDF: " + ex.getMessage(), Alert.AlertType.ERROR);
                }
            });
            
            container.getChildren().add(openButton);
            
            receiptPreviewBox.getChildren().add(container);
            
        } catch (Exception e) {
            e.printStackTrace();
            // Show error message
            Label errorLabel = new Label("Preview unavailable\n" + e.getMessage());
            errorLabel.setStyle("-fx-text-fill: #EF4444; -fx-font-size: 11px; -fx-padding: 20;");
            errorLabel.setWrapText(true);
            errorLabel.setTextAlignment(javafx.scene.text.TextAlignment.CENTER);
            receiptPreviewBox.getChildren().add(errorLabel);
        }
    }

    private void loadDefaults() throws IOException {
        if (!defaultsFile.exists()) return;
        Properties p = new Properties();
        try (FileInputStream fis = new FileInputStream(defaultsFile)) {
            p.load(fis);
        }

        sellerNameField.setText(p.getProperty("seller.name", sellerNameField.getText()));
        
        // Load address and phone if fields exist
        if (sellerAddressField != null) {
            sellerAddressField.setText(p.getProperty("seller.address", sellerAddressField.getText()));
        }
        if (sellerTaxIdField != null) {
            sellerTaxIdField.setText(p.getProperty("seller.taxId", sellerTaxIdField.getText()));
        }
        if (sellerPhoneField != null) {
            sellerPhoneField.setText(p.getProperty("seller.phone", sellerPhoneField.getText()));
        }
        
        sellerEmailField.setText(p.getProperty("seller.email", sellerEmailField.getText()));
        
        // Load logo from resources
        String hasLogo = p.getProperty("seller.hasLogo");
        if ("true".equals(hasLogo)) {
            File logoFile = new File("src/main/resources/img/logo.png");
            if (logoFile.exists()) {
                logoFilePath = logoFile.getAbsolutePath();
                if (logoFileLabel != null) {
                    logoFileLabel.setText("logo.png");
                }
                updateLogoPreview(logoFilePath);
            } else {
                if (logoFileLabel != null) {
                    logoFileLabel.setText("Logo file not found");
                }
            }
        }
        
        // Update receipt preview
        updateReceiptPreview();
        
        // load invoice counter if present (store is the next-to-use value)
        String ctr = p.getProperty("invoice.counter");
        if (ctr != null) {
            try {
                int v = Integer.parseInt(ctr);
                if (v >= 1 && v <= 9999) {
                    invoiceCounter = v;
                }
            } catch (NumberFormatException ignored) {}
        }
    }

    /**
     * 清空表单
     */
    @FXML
    private void handleClearForm() {
        Alert alert = new Alert(Alert.AlertType.CONFIRMATION);
        alert.setTitle("Confirm");
        alert.setHeaderText("Clear Form");
        alert.setContentText("Are you sure you want to clear all fields?");

        if (alert.showAndWait().get() == ButtonType.OK) {
            invoiceNumberField.setText(generateInvoiceNumber());
            invoiceDatePicker.setValue(LocalDate.now());
            notesArea.clear();

            sellerNameField.clear();
            sellerAddressField.clear();
            sellerTaxIdField.clear();
            sellerPhoneField.clear();
            sellerEmailField.clear();

            buyerNameField.clear();
            buyerAddressField.clear();
            buyerTaxIdField.clear();
            buyerPhoneField.clear();
            buyerEmailField.clear();

            items.clear();
            updateTotals();
            if (paidCheckBox != null) {
                paidCheckBox.setSelected(true);
            }
        }
    }

    /**
     * 加载示例数据
     */
    @FXML
    private void handleLoadSample() {
        invoiceNumberField.setText("INV-2025-SAMPLE");
        
        sellerNameField.setText("北京科技有限公司");
        sellerAddressField.setText("北京市朝阳区建国路88号");
        sellerTaxIdField.setText("91110000123456789X");
        sellerPhoneField.setText("010-12345678");
        sellerEmailField.setText("info@beijing-tech.com");

        buyerNameField.setText("上海商贸有限公司");
        buyerAddressField.setText("上海市浦东新区世纪大道100号");
        buyerTaxIdField.setText("91310000987654321Y");
        buyerPhoneField.setText("021-87654321");
        buyerEmailField.setText("contact@shanghai-trade.com");

        notesArea.setText("请在收到货物后7个工作日内付款。质保期为一年。");

        items.clear();
    items.add(new InvoiceItem("笔记本电脑 ThinkPad X1", 5, 8999.00, 0.0));
    items.add(new InvoiceItem("无线鼠标 罗技MX Master", 10, 699.00, 0.0));
    items.add(new InvoiceItem("机械键盘 Cherry MX", 8, 1299.00, 0.0));

        updateTotals();
        if (paidCheckBox != null) {
            paidCheckBox.setSelected(true);
        }
        showAlert("Info", "Sample data loaded", Alert.AlertType.INFORMATION);
    }

    /**
     * Navigation handler: switch to Generate page
     */
    @FXML
    public void handleNavGenerate() {
        showPage(pageGenerate);
        updateNavButtons("Generate");
    }

    /**
     * Navigation handler: switch to Seller Info page
     */
    @FXML
    public void handleNavSellerInfo() {
        showPage(pageSellerInfo);
        updateNavButtons("SellerInfo");
    }

    /**
     * Navigation handler: switch to Sales Items page
     */
    @FXML
    public void handleNavSalesItems() {
        showPage(pageSalesItems);
        updateNavButtons("SalesItems");
    }

    /**
     * Navigation handler: Export (placeholder)
     */
    @FXML
    public void handleNavExport() {
        showAlert("Export", "Export feature coming soon", Alert.AlertType.INFORMATION);
    }

    /**
     * Show a page in the stack and hide others
     */
    private void showPage(VBox page) {
        if (pageGenerate != null) pageGenerate.setVisible(false);
        if (pageSellerInfo != null) pageSellerInfo.setVisible(false);
        if (pageSalesItems != null) pageSalesItems.setVisible(false);
        if (page != null) page.setVisible(true);
    }

    /**
     * Update nav button active states
     */
    private void updateNavButtons(String active) {
        if (navGenerate != null) navGenerate.getStyleClass().remove("nav-btn-active");
        if (navSellerInfo != null) navSellerInfo.getStyleClass().remove("nav-btn-active");
        if (navSalesItems != null) navSalesItems.getStyleClass().remove("nav-btn-active");

        if ("Generate".equals(active) && navGenerate != null) navGenerate.getStyleClass().add("nav-btn-active");
        else if ("SellerInfo".equals(active) && navSellerInfo != null) navSellerInfo.getStyleClass().add("nav-btn-active");
        else if ("SalesItems".equals(active) && navSalesItems != null) navSalesItems.getStyleClass().add("nav-btn-active");
    }

    /**
     * Mode switch handler: Single Generate mode
     */
    @FXML
    public void handleModeSingle() {
        // Prevent redundant animations if already in Single mode
        if (isSingleMode) return;
        
        isSingleMode = true;
        
        // Update button styles
        if (modeButtonSingle != null && modeButtonBulk != null) {
            modeButtonSingle.getStyleClass().add("toggle-btn-active");
            modeButtonBulk.getStyleClass().remove("toggle-btn-active");
        }
        
        // Switch content with animation
        if (modeSingle != null && modeBulk != null) {
            switchModeWithAnimation(modeBulk, modeSingle, true);
        }
    }

    /**
     * Mode switch handler: Bulk Generate mode
     */
    @FXML
    public void handleModeBulk() {
        // Prevent redundant animations if already in Bulk mode
        if (!isSingleMode) return;
        
        isSingleMode = false;
        
        // Update button styles
        if (modeButtonSingle != null && modeButtonBulk != null) {
            modeButtonSingle.getStyleClass().remove("toggle-btn-active");
            modeButtonBulk.getStyleClass().add("toggle-btn-active");
        }
        
        // Switch content with animation
        if (modeSingle != null && modeBulk != null) {
            switchModeWithAnimation(modeSingle, modeBulk, false);
        }
    }
    
    /**
     * Animate the mode switch with slide effect
     * @param fromPane The pane to hide
     * @param toPane The pane to show
     * @param slideLeft True to slide left (Bulk to Single), false to slide right (Single to Bulk)
     */
    private void switchModeWithAnimation(VBox fromPane, VBox toPane, boolean slideLeft) {
        // Make both visible for animation
        fromPane.setVisible(true);
        toPane.setVisible(true);
        
        // Set initial positions
        double distance = 800; // Slide distance
        toPane.setTranslateX(slideLeft ? -distance : distance);
        toPane.setOpacity(0);
        
        // Create slide animations
        TranslateTransition slideOut = new TranslateTransition(Duration.millis(300), fromPane);
        slideOut.setToX(slideLeft ? distance : -distance);
        
        TranslateTransition slideIn = new TranslateTransition(Duration.millis(300), toPane);
        slideIn.setToX(0);
        
        // Create fade animations
        FadeTransition fadeOut = new FadeTransition(Duration.millis(200), fromPane);
        fadeOut.setToValue(0);
        
        FadeTransition fadeIn = new FadeTransition(Duration.millis(300), toPane);
        fadeIn.setToValue(1);
        
        // Combine animations
        ParallelTransition transition = new ParallelTransition(slideOut, slideIn, fadeOut, fadeIn);
        
        transition.setOnFinished(e -> {
            // Hide the old pane and reset positions
            fromPane.setVisible(false);
            fromPane.setTranslateX(0);
            fromPane.setOpacity(1);
            toPane.setTranslateX(0);
        });
        
        transition.play();
    }

    /**
     * 保存商品列表到文件
     */
    private void saveSavedItems() {
        try {
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            String json = gson.toJson(new ArrayList<>(savedItems));
            
            try (FileWriter writer = new FileWriter(savedItemsFile)) {
                writer.write(json);
            }
        } catch (IOException e) {
            System.err.println("Error saving items: " + e.getMessage());
        }
    }
    
    /**
     * 从文件加载商品列表
     */
    private void loadSavedItems() {
        if (!savedItemsFile.exists()) {
            return;
        }
        
        try (FileReader reader = new FileReader(savedItemsFile)) {
            Gson gson = new Gson();
            Type itemListType = new TypeToken<ArrayList<InvoiceItem>>(){}.getType();
            ArrayList<InvoiceItem> items = gson.fromJson(reader, itemListType);
            
            if (items != null) {
                savedItems.clear();
                savedItems.addAll(items);
                refreshSavedItemsList();
            }
        } catch (IOException e) {
            System.err.println("Error loading items: " + e.getMessage());
        }
    }

    /**
     * 显示提示框
     */
    private void showAlert(String title, String content, Alert.AlertType type) {
        Alert alert = new Alert(type);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(content);
        alert.showAndWait();
    }
}
