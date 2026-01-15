# Napa Valley AI Concierge

An embeddable AI-powered concierge chat widget for hotels and vacation rentals in Napa Valley.

## Quick Start

### 1. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
copy .env.example .env
# Then edit .env and add your Anthropic API key
```

### 2. Run the Server

```bash
cd backend
python main.py
```

The API will be running at `http://localhost:8000`

### 3. Test the Demo

Open `frontend/demo.html` in your browser. Click the chat bubble in the bottom-right corner to start talking to the AI concierge.

## For Hotels: How to Embed

Add this snippet to any website:

```html
<!-- Napa Concierge Widget -->
<link rel="stylesheet" href="https://your-domain.com/widget.css">
<script>
    window.NAPA_CONCIERGE_API = 'https://your-api-domain.com';
    window.NAPA_CONCIERGE_HOTEL = 'Your Hotel Name';
    window.NAPA_CONCIERGE_WELCOME = 'Custom welcome message here';
</script>
<script src="https://your-domain.com/widget.js"></script>
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `NAPA_CONCIERGE_API` | Backend API URL | `http://localhost:8000` |
| `NAPA_CONCIERGE_HOTEL` | Hotel name for personalization | `your hotel` |
| `NAPA_CONCIERGE_WELCOME` | Initial greeting message | Generic welcome |
| `NAPA_CONCIERGE_COLOR` | Primary brand color | `#722F37` (wine red) |

## API Endpoints

- `GET /` - Health check
- `POST /chat` - Send message and get response
- `GET /health` - Health status

## Project Structure

```
napa-concierge/
├── backend/
│   ├── main.py           # FastAPI server with Claude integration
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment template
├── frontend/
│   ├── widget.js         # Embeddable chat widget
│   ├── widget.css        # Widget styles
│   └── demo.html         # Demo hotel website
└── README.md
```

## Selling to Hotels

### Value Proposition
- 24/7 concierge service without staffing costs
- Personalized recommendations for every guest
- Increases guest satisfaction scores
- Reduces front desk workload
- Multilingual support

### Pricing Ideas
- $299/month for small B&Bs
- $499/month for boutique hotels
- $999/month for larger properties
- Add booking commission (5-10%) for reservations made through widget

## Future Enhancements

- [ ] Integration with reservation systems
- [ ] Admin dashboard for hotels
- [ ] Analytics and conversation insights
- [ ] Multi-language support
- [ ] Custom knowledge bases per hotel
- [ ] Booking capabilities
