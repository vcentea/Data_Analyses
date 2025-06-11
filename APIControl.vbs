Option Explicit

'========================
' IMPORTANT: Due to Excel UDF limitations, the LLM function cannot update cells directly.
' API calls are counted in memory and must be synced automatically using UpdateCallCount macro.
'========================

'========================
' Configuration Block
'========================
' LM Studio configuration
'Public Const API_ENDPOINT = "http://localhost:1234/v1/chat/completions"
'Public Const API_KEY = ""           ' Leave blank for LM Studio; fill for OpenAI
'Public Const DEFAULT_MODEL = "mistral-small-3.1-24b-instruct-2503"
'Public Const HTTP_TIMEOUTMS = 30000 ' Timeout in milliseconds

' Updated: Automatic update interval - changed to 2 seconds
Public Const AUTO_UPDATE_INTERVAL_SECONDS = 2 ' Update interval in seconds

' Uncomment the block below to switch to OpenRouter:
Public Const API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
Public Const API_KEY = "your-key-here"
Public Const DEFAULT_MODEL = "gpt-4.1-nano"
Public Const HTTP_TIMEOUTMS = 30000

'========================
' Module Variables
'========================
Private CallCountInMemory As Long
Private ResultCache As Object
Private NextUpdateTime As Date ' To store the time for the next scheduled update, used for cancellation
Private PreviousCallAPIStatus As String ' Track previous CallAPI status to detect changes
Private LimitReachedMessageShown As Boolean ' Track if limit reached message was already shown

'========================
' SINGLE SETUP MACRO - RUN THIS ONCE
'========================
Sub SetupAPIControl()
    Dim ws As Worksheet
    Set ws = ActiveSheet

    ' Check if already setup
    If ws.Range("A1").Value = "Call APIs:" Then
        MsgBox "API Control already set up! Stopping previous auto-updates.", vbInformation
        Call StopAutoUpdate ' Ensure any previous auto-update is stopped before re-setup
        Exit Sub
    End If

    ' Insert control row at the top of the active sheet
    ws.Rows(1).Insert

    ' Create control cells with proper values
    With ws
        .Range("A1").Value = "Call APIs:"
        .Range("B1").Value = "TRUE"
        .Range("C1").Value = "Max Calls:"
        .Range("D1").Value = 50
        .Range("E1").Value = "Current Calls:"
        .Range("F1").Value = 0 ' Initialize current calls to 0

        ' Add dropdown for TRUE/FALSE in cell B1 for easy toggling
        With .Range("B1").Validation
            .Delete ' Clear any existing validation
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                Operator:=xlBetween, Formula1:="TRUE,FALSE" ' List of allowed values
            .IgnoreBlank = True
            .InCellDropdown = True
        End With

        ' Format the control row for better visibility
        .Range("A1:F1").Font.Bold = True
        .Range("A1:F1").Interior.Color = RGB(240, 240, 240) ' Light grey background
        .Columns("A:F").AutoFit ' Adjust column widths to fit content
    End With

    ' Reset memory counter for API calls
    CallCountInMemory = 0
    
    ' Initialize tracking variables
    PreviousCallAPIStatus = "TRUE"
    LimitReachedMessageShown = False

    ' Inform the user about the setup and new automatic update
    MsgBox "API Control setup complete!" & vbCrLf & vbCrLf & _
            "• Set 'Call APIs' to FALSE to stop API calls" & vbCrLf & _
            "• Change 'Max Calls' to set your limit" & vbCrLf & _
            "• 'Current Calls' shows saved count (now updates automatically every " & AUTO_UPDATE_INTERVAL_SECONDS & " seconds)" & vbCrLf & _
            "• Memory count: " & CallCountInMemory & vbCrLf & _
            "• Counter will reset when switching from FALSE to TRUE", vbInformation

    ' Automatically start the update calls after setup
    Call StartAutoUpdate
End Sub

'========================
' Automatic Update Control Macros
' These macros manage the scheduling of the UpdateCallCount macro.
'========================
Sub StartAutoUpdate()
    ' Ensure any currently pending Application.OnTime event for UpdateCallCount is cancelled
    Call StopAutoUpdate

    ' Schedule the UpdateCallCount macro to run after the specified interval from now
    NextUpdateTime = Now + TimeSerial(0, 0, AUTO_UPDATE_INTERVAL_SECONDS)
    Application.OnTime EarliestTime:=NextUpdateTime, Procedure:="UpdateCallCount", Schedule:=True
    ' Output to Immediate Window for debugging purposes (Ctrl+G in VBA editor)
    Debug.Print "Scheduled next API call count update for: " & Format(NextUpdateTime, "hh:mm:ss")
End Sub

Sub StopAutoUpdate()
    On Error Resume Next ' Use On Error Resume Next to prevent error if no pending OnTime event exists
    ' Cancel the previously scheduled Application.OnTime event
    Application.OnTime EarliestTime:=NextUpdateTime, Procedure:="UpdateCallCount", Schedule:=False
    On Error GoTo 0 ' Reset error handling
    Debug.Print "Automatic API call count update stopped."
End Sub

'========================
' Update Macro (now called automatically by Application.OnTime)
' This macro syncs the in-memory API call count to the Excel sheet.
'========================
Sub UpdateCallCount()
    Dim ws As Worksheet
    Set ws = FindControlSheet()

    ' If the control sheet is not found, stop the automatic updates and alert the user.
    If ws Is Nothing Then
        MsgBox "Control row not found! Automatic update stopping. Please run SetupAPIControl first.", vbExclamation
        Call StopAutoUpdate ' Stop the auto-update completely as the control is missing
        Exit Sub
    End If

    Dim currentCalls As Long
    Dim maxCalls As Long
    Dim callsEnabled As String

    ' Retrieve current values from the control row on the sheet
    callsEnabled = UCase(Trim(ws.Range("B1").Value)) ' "TRUE" or "FALSE"
    currentCalls = Val(ws.Range("F1").Value)         ' Current API calls saved on sheet
    maxCalls = Val(ws.Range("D1").Value)             ' Maximum allowed API calls

    ' Check for status change from FALSE to TRUE and reset counter if needed
    If PreviousCallAPIStatus = "FALSE" And callsEnabled = "TRUE" Then
        ws.Range("F1").Value = 0 ' Reset current calls to 0
        CallCountInMemory = 0    ' Reset memory counter as well
        LimitReachedMessageShown = False ' Reset message flag when counter is reset
        Debug.Print "CallAPI status changed from FALSE to TRUE - counter reset to 0"
    Else
        ' Update the sheet's current calls by adding the in-memory count
        ws.Range("F1").Value = currentCalls + CallCountInMemory
    End If
    
    ' Update the previous status for next comparison
    PreviousCallAPIStatus = callsEnabled

    ' Check if limit is reached and disable API calls (but keep timer running)
    If (Val(ws.Range("F1").Value)) >= maxCalls Then
        ws.Range("B1").Value = "FALSE" ' Set toggle to FALSE if limit is reached
        ' Only show message once when limit is first reached
        If Not LimitReachedMessageShown Then
            MsgBox "API call limit reached. You can manually reset, change the limit, or toggle back to TRUE to reset.", vbInformation
            LimitReachedMessageShown = True
        End If
    End If

    ' Reset memory counter *after* updating the sheet but *before* rescheduling.
    ' This ensures only newly accumulated calls are counted in the next interval.
    CallCountInMemory = 0

    ' Always re-schedule to continue monitoring, regardless of status or limits
    ' This allows detection of status changes and limit modifications
    Call StartAutoUpdate

    ' Note: The MsgBox for "Call count updated!" has been removed here to prevent
    ' annoying pop-ups every 2 seconds during automatic operation.
    ' The updates are visible directly in cell F1.
End Sub

'========================
' Manual Utility Macros
' These macros provide manual control and information.
'========================
Sub ShowMemoryCount()
    MsgBox "Unsaved API calls in memory: " & CallCountInMemory, vbInformation, "Memory Count"
End Sub

Sub ResetCounter()
    Dim ws As Worksheet
    Set ws = FindControlSheet()

    If ws Is Nothing Then
        MsgBox "Control row not found! Please run SetupAPIControl first.", vbExclamation
        Exit Sub
    End If

    ws.Range("F1").Value = 0     ' Reset current calls on sheet to 0
    ws.Range("B1").Value = "TRUE" ' Re-enable API calls
    CallCountInMemory = 0        ' Reset in-memory counter
    PreviousCallAPIStatus = "TRUE" ' Reset status tracking
    LimitReachedMessageShown = False ' Reset message flag

    MsgBox "Counter reset to 0 and API calls enabled! Timer continues running.", vbInformation
End Sub

'========================
' Helper Functions
' These functions assist the main LLM functionality and API control.
'========================
Private Sub InitializeCache()
    If ResultCache Is Nothing Then
        Set ResultCache = CreateObject("Scripting.Dictionary")
    End If
End Sub

Private Function GetCacheKey(prompt As String, temperature As Double, model As String) As String
    GetCacheKey = prompt & "|" & CStr(temperature) & "|" & model
End Function

Private Function FindControlSheet() As Worksheet
    Dim ws As Worksheet

    ' First, check if the active sheet contains the control row
    Set ws = ActiveSheet
    If ws.Range("A1").Value = "Call APIs:" Then
        Set FindControlSheet = ws
        Exit Function
    End If

    ' If not found on the active sheet, search all worksheets in the workbook
    For Each ws In ThisWorkbook.Worksheets
        If ws.Range("A1").Value = "Call APIs:" Then
            Set FindControlSheet = ws ' Found the control sheet
            Exit Function
        End If
    Next ws

    Set FindControlSheet = Nothing ' Control sheet not found in the workbook
End Function

Private Function CanCallAPI() As Boolean
    Dim ws As Worksheet
    Set ws = FindControlSheet()

    ' If control sheet is not found, API calls are disabled
    If ws Is Nothing Then
        CanCallAPI = False
        Exit Function
    End If

    Dim callsEnabled As String
    Dim currentCalls As Long
    Dim maxCalls As Long

    ' Get the status of API calls and limits from the control row
    callsEnabled = UCase(Trim(ws.Range("B1").Value))          ' "TRUE" or "FALSE"
    currentCalls = Val(ws.Range("F1").Value) + CallCountInMemory ' Total calls including unsaved in memory
    maxCalls = Val(ws.Range("D1").Value)                      ' Maximum allowed calls

    ' Determine if an API call can be made based on enablement and limit
    CanCallAPI = (callsEnabled = "TRUE" And currentCalls < maxCalls)
End Function

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

'========================
' Helper: RemoveThinkingTags
' This function removes specific XML-like tags from the LLM's response.
'========================
Function RemoveThinkingTags(text As String) As String
    Dim result As String
    result = text

    Dim startPos As Long
    Dim endPos As Long

    ' Remove <think>...</think> blocks
    Do
        startPos = InStr(result, "<think>")
        If startPos = 0 Then Exit Do ' No more <think> tags

        endPos = InStr(startPos, result, "</think>")
        If endPos = 0 Then Exit Do ' Mismatched tag, exit

        Dim afterThink As String
        afterThink = Mid(result, endPos + 8) ' Text after </think>

        ' Remove leading newline if it follows the tag
        If Left(afterThink, 2) = "\n" Then
            afterThink = Mid(afterThink, 3)
        End If

        ' Reconstruct the string without the <think> block
        If startPos > 1 Then
            result = Left(result, startPos - 1) & afterThink
        Else
            result = afterThink
        End If
    Loop

    ' Remove <thinking>...</thinking> blocks (similar logic)
    Do
        startPos = InStr(result, "<thinking>")
        If startPos = 0 Then Exit Do

        endPos = InStr(startPos, result, "</thinking>")
        If endPos = 0 Then Exit Do

        Dim afterThinking As String
        afterThinking = Mid(result, endPos + 11)

        If Left(afterThinking, 2) = "\n" Then
            afterThinking = Mid(afterThinking, 3)
        End If

        If startPos > 1 Then
            result = Left(result, startPos - 1) & afterThinking
        Else
            result = afterThinking
        End If
    Loop

    RemoveThinkingTags = result
End Function

'========================
' Helper: JsonEscape
' Escapes special characters in a string for JSON format.
'========================
Function JsonEscape(text As String) As String
    Dim i As Long
    Dim ch As String * 1
    Dim out As String

    For i = 1 To Len(text)
        ch = Mid(text, i, 1)
        Select Case ch
            Case "\": out = out & "\\"  ' Escape backslash
            Case """": out = out & "\""" ' Escape double quote
            Case vbCr: out = out & "\r"  ' Escape carriage return
            Case vbLf: out = out & "\n"  ' Escape newline
            Case Else: out = out & ch    ' Append other characters as is
        End Select
    Next i

    JsonEscape = out
End Function

'========================
' Helper: JsonUnescape
' Unescapes JSON special characters in a string.
' This function is not directly used in the LLM UDF but is included for completeness.
'========================
Function JsonUnescape(text As String) As String
    Dim i As Long
    Dim ch As String * 1
    Dim out As String
    i = 1

    Do While i <= Len(text)
        ch = Mid(text, i, 1)
        If ch = "\" And i < Len(text) Then
            i = i + 1 ' Move to the next character to check for escape sequence
            ch = Mid(text, i, 1)
            Select Case ch
                Case "\": out = out & "\"  ' Unescape \\ to \
                Case """": out = out & """" ' Unescape \" to "
                Case "r": out = out & vbCr  ' Unescape \r to carriage return
                Case "n": out = out & vbLf  ' Unescape \n to newline
                Case Else: out = out & ch    ' If not a known escape, append the character after backslash
            End Select
        Else
            out = out & ch ' Append regular character
        End If
        i = i + 1
    Loop

    JsonUnescape = out
End Function 