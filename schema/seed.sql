-- Seed data for demo purposes

INSERT INTO customer (id, full_name, email, phone, pan_number, aadhar_number, date_of_birth, address) VALUES
(1, 'Rahul Sharma', 'rahul.sharma@email.com', '9876543210', 'ABCDE1234F', '1234-5678-9012', '1995-06-15', '42 MG Road, Bangalore'),
(2, 'Priya Patel', 'priya.patel@email.com', '9876543211', 'FGHIJ5678K', '2345-6789-0123', '1992-03-22', '15 Park Street, Mumbai'),
(3, 'Amit Kumar', 'amit.kumar@email.com', '9876543212', 'KLMNO9012P', '3456-7890-1234', '1998-11-08', '78 Anna Salai, Chennai')
ON CONFLICT DO NOTHING;

INSERT INTO account (id, customer_id, account_number, account_type, balance) VALUES
(1, 1, 'ACC-2024-001', 'savings', 125000.00),
(2, 1, 'ACC-2024-002', 'current', 450000.00),
(3, 2, 'ACC-2024-003', 'savings', 89000.00),
(4, 3, 'ACC-2024-004', 'savings', 235000.00),
(5, 3, 'ACC-2024-005', 'fixed_deposit', 500000.00)
ON CONFLICT DO NOTHING;

INSERT INTO transaction (account_id, txn_type, amount, description, reference_id) VALUES
(1, 'credit', 50000.00, 'Salary credit - September', 'TXN-001'),
(1, 'debit', 5000.00, 'ATM withdrawal', 'TXN-002'),
(1, 'debit', 2500.00, 'Electricity bill payment', 'TXN-003'),
(2, 'credit', 150000.00, 'Business payment received', 'TXN-004'),
(2, 'debit', 30000.00, 'Vendor payment', 'TXN-005'),
(3, 'credit', 35000.00, 'Salary credit - September', 'TXN-006'),
(3, 'debit', 8000.00, 'Online shopping', 'TXN-007'),
(4, 'credit', 45000.00, 'Salary credit - September', 'TXN-008')
ON CONFLICT DO NOTHING;

INSERT INTO loan (customer_id, loan_type, principal, interest_rate, tenure_months, emi, status) VALUES
(1, 'home', 3500000.00, 8.50, 240, 30345.00, 'disbursed'),
(2, 'personal', 200000.00, 12.00, 36, 6643.00, 'approved'),
(3, 'education', 800000.00, 9.00, 60, 16607.00, 'pending')
ON CONFLICT DO NOTHING;

INSERT INTO card (customer_id, card_number, card_type, credit_limit, outstanding, status, expiry_date) VALUES
(1, 'XXXX-XXXX-XXXX-4521', 'credit', 200000.00, 35000.00, 'active', '2027-12-31'),
(1, 'XXXX-XXXX-XXXX-7834', 'debit', NULL, NULL, 'active', '2028-06-30'),
(2, 'XXXX-XXXX-XXXX-9156', 'credit', 150000.00, 12000.00, 'active', '2027-09-30'),
(3, 'XXXX-XXXX-XXXX-2367', 'debit', NULL, NULL, 'blocked', '2028-03-31')
ON CONFLICT DO NOTHING;

INSERT INTO complaint (customer_id, category, subject, description, status, priority) VALUES
(1, 'transaction', 'Failed UPI payment', 'Amount debited but not credited to merchant. TXN ref: UPI-789456', 'open', 'high'),
(2, 'card', 'Unauthorized transaction', 'Found unknown charge of Rs 5000 on credit card', 'in_progress', 'critical')
ON CONFLICT DO NOTHING;

