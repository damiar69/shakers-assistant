# Security & Privacy on Shakers

Shakers takes user security and privacy very seriously. Here are the key points:

## 1. Secure Connection (SSL/TLS)
- All requests are made via HTTPS (TLS v1.2+).  
- Sensitive data (passwords, tokens) are encrypted in transit.

## 2. Password Storage
- Passwords are stored in the database with strong hashing (bcrypt with salt).  
- We do not store passwords in plain text.

## 3. Access to Private Files
- Private documents (contracts, NDA) are stored in AWS S3 with restricted access policies.  
- Each file is protected by a “signed URL” that expires in 24 hours.

## Customer Data Confidentiality
- Clients can mark a project as “confidential” to hide details until a freelancer is selected.  
- The content of private messages is not shared with third parties.

## 5. Privacy Policy
- We do not sell or share personal information with advertisers.  
- We use Google Analytics for anonymous (aggregated) statistics only.

> **Recommendation**: Change your password periodically and enable 2FA if your account has access to large projects.

For tips on writing effective search queries, see our [search best practices](https://example.com/shakers/security_and_privacy).
