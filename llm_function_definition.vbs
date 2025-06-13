'========================
' Main Function: LLM
' This is the User-Defined Function (UDF) called from Excel cells.
'========================
Function LLM(prompt As String, Optional temperature As Double = 0.1, Optional model As String = "") As String
    On Error GoTo Fail ' Enable error handling

    ' Initialize the cache for storing results if not already initialized
    Call InitializeCache

    ' Create a unique key for caching based on prompt, temperature, and model
    Dim cacheKey As String
    cacheKey = GetCacheKey(prompt, temperature, model)

    ' Check if an API call is allowed based on sheet settings and call limits
    If Not CanCallAPI() Then
        ' If API calls are not allowed, try to return a cached result
        If ResultCache.Exists(cacheKey) Then
            LLM = ResultCache(cacheKey) ' Return cached result
        Else
            LLM = "#NO_API (Memory: " & CallCountInMemory & " unsaved calls)" ' Indicate no API call was made
        End If
        Exit Function ' Exit the function
    End If

    ' Determine the model to use; prefer explicit model, otherwise use default
    Dim chosenModel As String
    If model = "" Then
        chosenModel = DEFAULT_MODEL
    Else
        chosenModel = model
    End If

    ' Build the JSON payload for the API request
    Dim escapedPrompt As String
    escapedPrompt = JsonEscape(prompt) ' Escape special characters in the prompt for JSON
    Dim tempStr As String
    tempStr = Replace(CStr(temperature), ",", ".") ' Ensure decimal separator is a dot for JSON

    Dim payload As String
    payload = "{""model"":""" & chosenModel & """," & _
              """messages"":[{""role"":""user"",""content"":""" & escapedPrompt & """}]," & _
              """temperature"":" & tempStr & "}"

    ' Create an HTTP request object
    Dim httpReq As Object
    On Error Resume Next ' Temporarily disable error handling for object creation
    Set httpReq = CreateObject("WinHttp.WinHttpRequest.5.1") ' Preferred for robustness
    If httpReq Is Nothing Then Set httpReq = CreateObject("MSXML2.ServerXMLHTTP.6.0") ' Fallback
    If httpReq Is Nothing Then Set httpReq = CreateObject("MSXML2.XMLHTTP")         ' Last resort
    On Error GoTo Fail ' Re-enable error handling

    ' Set timeouts for the HTTP request to prevent indefinite waiting
    On Error Resume Next
    ' SetTimeouts parameters: Resolve, Connect, Send, Receive (all in milliseconds)
    CallByName httpReq, "SetTimeouts", VbMethod, 0, HTTP_TIMEOUTMS, HTTP_TIMEOUTMS, HTTP_TIMEOUTMS
    On Error GoTo Fail

    ' Send the HTTP request
    httpReq.Open "POST", API_ENDPOINT, False ' False for synchronous call (required for UDFs)
    httpReq.setRequestHeader "Content-Type", "application/json" ' Set content type header
    If API_KEY <> "" Then
        httpReq.setRequestHeader "Authorization", "Bearer " & API_KEY ' Add API key if provided
    End If
    httpReq.Send payload ' Send the JSON payload

    ' Increment the in-memory call counter.
    ' This is done here because UDFs cannot directly write to cells.
    CallCountInMemory = CallCountInMemory + 1

    ' Handle the response from the API
    Dim status As Long
    status = httpReq.Status ' Get HTTP status code (e.g., 200 for success)
    Dim responseText As String
    responseText = httpReq.ResponseText ' Get the full response body

    If status <> 200 Then
        ' If the status is not 200 (OK), return an error message
        If Len(responseText) > 300 Then
            LLM = "#HTTP" & status & ": " & Left(responseText, 300) & "..." ' Truncate long error messages
        Else
            LLM = "#HTTP" & status & ": " & responseText
        End If
        Exit Function
    End If

    ' Parse the JSON response to extract the 'content'
    Dim pos As Long
    ' Find the start of the "content" field
    pos = InStr(responseText, """content"":")
    If pos = 0 Then
        LLM = "#PARSE? (Content not found)" ' Error if "content" field is missing
        Exit Function
    End If

    ' Find the start of the actual content string (after "content":" )
    Dim startQuotePos As Long
    startQuotePos = InStr(pos + Len("""content"":"), responseText, """")
    If startQuotePos = 0 Then
        LLM = "#PARSE? (Opening quote missing)" ' Error if opening quote is missing
        Exit Function
    End If

    ' Extract content by manually parsing the string, handling escaped characters
    Dim result As String
    Dim ch As String * 1
    Dim idx As Long
    Dim inEscape As Boolean ' Flag to track if the current character is escaped
    idx = startQuotePos + 1 ' Start reading after the opening quote
    inEscape = False

    Do While idx <= Len(responseText)
        ch = Mid(responseText, idx, 1)

        If inEscape Then
            result = result & ch ' Append the escaped character directly
            inEscape = False    ' Reset escape flag
        ElseIf ch = "\" Then
            result = result & ch ' Append backslash and set escape flag
            inEscape = True
        ElseIf ch = """" Then
            Exit Do ' Found the closing quote, exit loop
        Else
            result = result & ch ' Append regular character
        End If

        idx = idx + 1
    Loop

    ' Clean up the extracted result (remove thinking tags, unescape characters)
    result = RemoveThinkingTags(result) ' Remove specific XML-like tags

    ' Remove leading newline characters if present
    If Left(result, 2) = "\n" Then
        result = Mid(result, 3)
    End If

    ' Unescape common JSON escaped characters
    result = Replace(result, "\""", """") ' Unescape double quotes
    result = Replace(result, "\\", "\")   ' Unescape backslashes
    result = Replace(result, "\n", vbLf)  ' Convert \n to VBA newline
    result = Replace(result, "\r", vbCr)  ' Convert \r to VBA carriage return

    result = Trim(result) ' Trim leading/trailing spaces

    ' Cache the successfully retrieved result
    ResultCache(cacheKey) = result

    LLM = result ' Assign the final result to the function
    Exit Function ' Exit on success

Fail:
    ' Generic error handler
    LLM = "#ERR" & Err.Number & ": " & Err.Description
End Function 