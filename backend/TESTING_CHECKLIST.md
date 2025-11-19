# Local Testing Checklist for StateGraph Supervisor

## ✅ Pre-Push Testing Guide

Before pushing the new StateGraph supervisor to your branch, follow these steps to ensure everything works correctly.

---

## 1. Unit Tests (Required) ✅

**Status: COMPLETE - All 15 tests passing**

```bash
cd backend
./venv/bin/python3.11 -m pytest tests/test_stategraph_supervisor.py tests/test_app_basic.py -v
```

**Expected Result:**
- ✅ 15/15 tests passing
- ✅ No errors, only deprecation warnings (safe to ignore)

---

## 2. Start Local Server (Required)

### Option A: Using the start script
```bash
cd backend
./start.sh
```

### Option B: Manual start
```bash
cd backend
./venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
2025-11-15 XX:XX:XX - agents.scheduler - INFO - Google Calendar Scheduler agent initialized with OAuth support
✅ StateGraph-based supervisor loaded successfully
✅ Successfully imported agent_app
✅ Successfully imported configuration
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**If you see an ImportError:**
- Make sure you're using the venv Python: `./venv/bin/uvicorn`
- Check that langchain 1.0.0 is installed: `./venv/bin/pip list | grep langchain`

---

## 3. Integration Tests (Automated)

With the server running, open a **new terminal** and run:

```bash
cd backend
./venv/bin/python3.11 test_local.py
```

This will test:
1. ✅ Health check endpoint
2. ✅ User authentication
3. ✅ General chat (tests general response agent)
4. ✅ Schedule query (tests Scheduler agent routing)
5. ✅ Assignment query (tests Project Manager agent routing)
6. ✅ Streaming endpoint

**Expected Result:** All 6 tests should pass

---

## 4. Manual Testing (Optional but Recommended)

### Test 1: Health Check
```bash
curl http://localhost:8000/
```
**Expected:** `{"status": "healthy", "agent_loaded": true}`

### Test 2: General Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Hello, what can you help me with?",
    "user_id": "test-user"
  }'
```
**Expected:** JSX-formatted response with `<>` and `</>`

### Test 3: Schedule Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "What is on my calendar today?",
    "user_id": "test-user"
  }'
```
**Expected:** JSX response mentioning calendar/events

### Test 4: Assignment Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Show me my assignments",
    "user_id": "test-user"
  }'
```
**Expected:** JSX response about assignments/tasks

---

## 5. Check Logs for Issues

While the server is running, watch for:

### ✅ Good Signs:
```
✅ StateGraph-based supervisor loaded successfully
INFO - Google Calendar Scheduler agent initialized
```

### ⚠️ Warning Signs (investigate if you see these):
```
❌ Failed to import agent_app
❌ ImportError: cannot import name 'ToolRuntime'
❌ Agent invocation error
```

---

## 6. Test with Frontend (If Available)

If you have the frontend running:

1. Start backend: `./start.sh`
2. Start frontend: `cd ../frontend/flowstate && npm run dev`
3. Navigate to chat interface
4. Try these queries:
   - "Hello, what can you help with?" (general)
   - "What's on my schedule?" (scheduler)
   - "Show my assignments" (project manager)

**Expected:** All responses should be properly formatted in the UI

---

## 7. Performance Check

Run this quick performance test:

```bash
time curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Hello", "user_id": "test"}'
```

**Expected:** Response time < 5 seconds

---

## 8. Database Connections (If Using Notion/Google Calendar)

Check that OAuth integrations still work:

```bash
curl http://localhost:8000/api/oauth/notion/status \
  -H "Authorization: Bearer YOUR_TOKEN"

curl http://localhost:8000/api/oauth/google-calendar/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### Issue: Server won't start
**Solution:**
```bash
cd backend
./venv/bin/pip install -r requirements.txt --force-reinstall
./start.sh
```

### Issue: ImportError for ToolRuntime
**Solution:**
```bash
./venv/bin/pip install "langchain==1.0.0" --force-reinstall
```

### Issue: Agent not responding
**Check:**
1. Is Anthropic API key set? `echo $ANTHROPIC_API_KEY`
2. Are environment variables loaded? Check `.env` file
3. Look at server logs for specific errors

### Issue: Tests failing
**Debug:**
```bash
# Run tests with verbose output
./venv/bin/python3.11 -m pytest tests/test_stategraph_supervisor.py -vv -s

# Check specific test
./venv/bin/python3.11 -m pytest tests/test_stategraph_supervisor.py::test_supervisor_routing_scheduler -vv
```

---

## Pre-Push Checklist

Before pushing to your branch:

- [ ] All unit tests pass (15/15)
- [ ] Server starts without errors
- [ ] Health check returns `agent_loaded: true`
- [ ] At least one chat query works
- [ ] Response is JSX formatted (`<>...</>`)
- [ ] No errors in server logs
- [ ] Integration tests pass (6/6)

---

## What to Commit

### ✅ Files to commit:
- `agents/supervisor.py` (new StateGraph implementation)
- `app.py` (updated to use AgentState)
- `requirements.txt` (pinned langchain==1.0.0)
- `tests/test_stategraph_supervisor.py` (new tests)
- `validate_types.py` (validation script)
- `test_local.py` (integration tests)
- `start.sh` (startup script)
- `PRIORITY_1_COMPLETE.md` (documentation)

### ⚠️ Files to keep but not commit (unless you want them):
- `agents/supervisor_old.py` (backup)
- `agents/supervisor.py.backup` (backup)

### ❌ Files to ignore:
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `.langgraph_api/` (already in .gitignore)

---

## Next Steps After Testing

Once local testing passes:

1. **Commit your changes:**
```bash
git add agents/supervisor.py app.py requirements.txt tests/
git commit -m "feat: implement StateGraph multi-agent architecture with enforced response formatting"
```

2. **Push to your branch:**
```bash
git push origin your-branch-name
```

3. **Test in pre-production:**
   - Deploy to staging environment
   - Run same integration tests
   - Monitor logs for 24 hours
   - Check response consistency

4. **Proceed with Priority 2-6:**
   - Context builder utility
   - Prompt simplification
   - Additional optimizations

---

## Questions?

If you encounter issues:
1. Check the `PRIORITY_1_COMPLETE.md` for detailed explanations
2. Review the test output carefully
3. Check server logs for specific errors
4. Verify environment variables are set

**The type checking warnings in your IDE are SAFE TO IGNORE** - they don't affect runtime!
