# FMCSA Data Scraper

## Overview

This is a web-based scraper application for extracting transportation company data from the Federal Motor Carrier Safety Administration (FMCSA) database. The application allows users to scrape motor carrier information by MC number ranges and export the collected data in multiple formats. It features a real-time web interface with live progress updates and data visualization.

**Main Entry Point**: `app.py` - Run this file to start the Flask web server

**Recent Update (Aug 5, 2025)**: 
- Cleaned up project structure by removing all desktop-related files
- Application is now exclusively web-based with Flask frontend
- **Major Authentication Overhaul**: Replaced Google OAuth with simple license key + email verification system
- Added two-step login process: license key validation followed by email verification
- License keys are validated against Google Sheets database in real-time
- Added professional contact information panel with configurable email and WhatsApp details
- Simplified session management using Flask sessions instead of user database
- **Background License Monitoring**: Added automatic license expiry checking every 1 minute
- Real-time license expiry notifications with automatic access blocking
- Professional expiry modal with contact information and countdown timer

**Critical Fix (Aug 2, 2025)**: Resolved major accuracy issue where inactive MC numbers were returning incorrect data from other carriers. Fixed fallback search logic to only search by MC number (not USDOT), properly detect inactive/not found records, and validate MC number matches to prevent data cross-contamination.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Pure HTML/CSS/JavaScript with Bootstrap 5 for UI components
- **Real-time Communication**: Socket.IO for bidirectional client-server communication
- **Design Pattern**: Single-page application with responsive Bootstrap grid layout
- **User Interface**: Split-pane design with control panel on left and data table on right
- **State Management**: Client-side JavaScript manages scraping state and data display

### Backend Architecture
- **Framework**: Flask web framework with Flask-SocketIO for WebSocket support
- **Authentication**: Session-based authentication with license key validation
- **License Validation**: Real-time validation against Google Sheets database via CSV export
- **Threading Model**: Background threading for non-blocking scraping operations
- **Session Management**: HTTP sessions for maintaining user authentication and scraper state
- **Data Processing**: In-memory storage with CSV/export capabilities
- **Error Handling**: Centralized error handling with real-time user notifications

### Web Scraping Engine
- **Library**: Requests library with BeautifulSoup for HTML parsing
- **Session Management**: Persistent HTTP sessions with browser-like headers
- **Rate Limiting**: Built-in delays and polite scraping practices
- **Target**: FMCSA's public motor carrier database
- **Data Extraction**: Structured data extraction from carrier profile pages

### Data Storage
- **Primary Storage**: In-memory Python lists during scraping
- **Export Formats**: CSV, XLSX, and TXT file generation
- **State Management**: Global variables for scraping state and collected data
- **No Persistent Database**: Data exists only during application runtime

### Communication Layer
- **WebSocket Protocol**: Socket.IO for real-time progress updates
- **Event-Driven**: Asynchronous event handling for scraping lifecycle
- **Progress Tracking**: Live status updates and data streaming to frontend
- **Error Propagation**: Real-time error notifications to user interface

## External Dependencies

### Python Libraries
- **Flask**: Web framework for HTTP server and routing
- **Flask-SocketIO**: WebSocket implementation for real-time communication
- **Requests**: HTTP client library for web scraping
- **BeautifulSoup**: HTML parsing and data extraction
- **Threading**: Python standard library for concurrent operations

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive UI components
- **Font Awesome**: Icon library for user interface elements
- **Socket.IO Client**: JavaScript client for WebSocket communication

### Target External Service
- **FMCSA Database**: Federal Motor Carrier Safety Administration public database
- **No Authentication Required**: Public access to carrier information
- **Rate Limiting Considerations**: Respectful scraping with delays between requests

### Development Dependencies
- **Environment Variables**: SECRET_KEY configuration for Flask sessions
- **No Database**: Application operates without persistent storage requirements