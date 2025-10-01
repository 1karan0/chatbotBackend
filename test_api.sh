#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
TOKEN=""

echo "=================================="
echo "API Testing Script"
echo "=================================="
echo ""

# Check if server is running
echo "1. Checking if server is running..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
if [ "$health_response" == "200" ]; then
    echo -e "${GREEN}✅ Server is running${NC}"
else
    echo -e "${RED}❌ Server is not running. Start it with: python3 main.py${NC}"
    exit 1
fi
echo ""

# Create tenant
echo "2. Creating test tenant..."
create_tenant_response=$(curl -s -X POST "${BASE_URL}/auth/tenants" \
    -H "Content-Type: application/json" \
    -d '{
        "tenant_id": "test_tenant_'$(date +%s)'",
        "tenant_name": "Test Company",
        "username": "testuser",
        "password": "testpass123"
    }')

if echo "$create_tenant_response" | grep -q "user_id"; then
    echo -e "${GREEN}✅ Tenant created successfully${NC}"
    echo "$create_tenant_response" | head -c 100
    echo "..."
else
    echo -e "${YELLOW}⚠️  Tenant creation response: ${NC}"
    echo "$create_tenant_response"
fi
echo ""

# Login
echo "3. Logging in..."
login_response=$(curl -s -X POST "${BASE_URL}/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=testpass123")

TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$TOKEN" ]; then
    echo -e "${GREEN}✅ Login successful${NC}"
    echo "Token: ${TOKEN:0:20}..."
else
    echo -e "${RED}❌ Login failed${NC}"
    echo "Response: $login_response"
    exit 1
fi
echo ""

# Add text source
echo "4. Adding text knowledge source..."
text_response=$(curl -s -X POST "${BASE_URL}/knowledge/sources/text" \
    -H "Authorization: Bearer $TOKEN" \
    -F "text=Our company provides AI chatbot services. We are open Monday to Friday, 9 AM to 5 PM. Contact us at support@example.com" \
    -F "title=Company Info")

if echo "$text_response" | grep -q "completed"; then
    echo -e "${GREEN}✅ Text source added successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Text source response: ${NC}"
    echo "$text_response"
fi
echo ""

# Wait for indexing
echo "5. Waiting for indexing..."
sleep 2
echo -e "${GREEN}✅ Ready${NC}"
echo ""

# Ask a question
echo "6. Asking a question..."
question_response=$(curl -s -X POST "${BASE_URL}/chat/ask" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "What are your business hours?"}')

if echo "$question_response" | grep -q "answer"; then
    echo -e "${GREEN}✅ Question answered successfully${NC}"
    echo ""
    echo "Answer:"
    echo "$question_response" | grep -o '"answer":"[^"]*"' | cut -d'"' -f4
else
    echo -e "${RED}❌ Failed to get answer${NC}"
    echo "Response: $question_response"
fi
echo ""

# Get chat status
echo "7. Checking chat status..."
status_response=$(curl -s -X GET "${BASE_URL}/chat/status" \
    -H "Authorization: Bearer $TOKEN")

if echo "$status_response" | grep -q "document_count"; then
    echo -e "${GREEN}✅ Status retrieved${NC}"
    echo "$status_response"
else
    echo -e "${YELLOW}⚠️  Status response: ${NC}"
    echo "$status_response"
fi
echo ""

# List knowledge sources
echo "8. Listing knowledge sources..."
sources_response=$(curl -s -X GET "${BASE_URL}/knowledge/sources" \
    -H "Authorization: Bearer $TOKEN")

if echo "$sources_response" | grep -q "source_id"; then
    echo -e "${GREEN}✅ Sources listed successfully${NC}"
    source_count=$(echo "$sources_response" | grep -o "source_id" | wc -l)
    echo "Found $source_count source(s)"
else
    echo -e "${YELLOW}⚠️  Sources response: ${NC}"
    echo "$sources_response"
fi
echo ""

echo "=================================="
echo "Test Summary"
echo "=================================="
echo -e "${GREEN}✅ All basic tests completed!${NC}"
echo ""
echo "Next steps:"
echo "  - Try uploading files via /knowledge/sources/file"
echo "  - Try adding URLs via /knowledge/sources/url"
echo "  - Access Swagger UI at ${BASE_URL}/docs"
echo ""
