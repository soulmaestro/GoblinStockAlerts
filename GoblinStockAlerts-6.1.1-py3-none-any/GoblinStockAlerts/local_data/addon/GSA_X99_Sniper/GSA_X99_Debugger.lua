-- --------------------------------------------------------------------------------------------
-- Constants
-- --------------------------------------------------------------------------------------------

GSARed = 1
GSAYellow = 2
GSACyan = 3
GSAGreen = 4
GSAPurple = 5

X99Debugger_Regular = 0
X99Debugger_Extended = 1

X99Console_Read = 0
X99Console_Copy = 1

-- --------------------------------------------------------------------------------------------
-- Addon functions
-- --------------------------------------------------------------------------------------------

function X99Debugger:Print(msg, color, level)
  level = level or X99Debugger_Regular
  if level == X99Debugger_Extended and not self.Extended then
    return
  end

  if color == GSARed then
    self.Console:AddMessage(msg, 1, 0, 0)
  elseif color == GSAYellow then
    self.Console:AddMessage(msg, 1, 1, 0)
  elseif color == GSACyan then
    self.Console:AddMessage(msg, 0, 1, 1)
  elseif color == GSAGreen then
    self.Console:AddMessage(msg, 0, 1, 0)
  elseif color == GSAPurple then
    self.Console:AddMessage(msg, 1, 0, 1)
  else
    self.Console:AddMessage(msg)
  end
  self.Console:UpdateScrollbar()
end

function X99Debugger:SetExtendedMode(enabled)
  self.Extended = enabled
  if enabled then
    self:Print("Extended debug info is now enabled", GSAYellow)
  else
    self:Print("Extended debug info is now disabled", GSAYellow)
  end
end

function X99DebuggerConsole:UpdateScrollbar()
	local numMessages = self:GetNumMessages();
	local maxValue = math.max(numMessages, 1);
	self.ScrollBar:SetMinMaxValues(1, maxValue);
	self.ScrollBar:SetValue(maxValue - self:GetScrollOffset());
end

function X99Debugger:ScrollBy(value, userInput)
	self.ScrollUp:Enable();
	self.ScrollDown:Enable();

	local minVal, maxVal = self:GetMinMaxValues();
	if value >= maxVal then
		self.thumbTexture:Show();
		self.ScrollDown:Disable()
	end
	if value <= minVal then
		self.thumbTexture:Show();
		self.ScrollUp:Disable();
	end

	if userInput then
		self:GetParent():SetScrollOffset(maxVal - value);
	end
end

function X99Debugger_ToggleConsole()
  if X99Debugger.Mode == X99Console_Copy then
    X99DebuggerCopyClose:SetText("Copy")
    X99Debugger.Mode = X99Console_Read
    X99Debugger.CopyBox:Hide()
    X99Debugger.CopyBox.Clipboard:SetText("")
    X99Debugger.Console:Show()
  else
    X99Debugger.Mode = X99Console_Copy
    X99DebuggerCopyClose:SetText("Back")
    X99Debugger.Console:Hide()
    for i = 1, X99Debugger.Console:GetNumMessages() do
      local msg = X99Debugger.Console:GetMessageInfo(i)
      X99Debugger.CopyBox.Clipboard:Insert(msg .. "\n")
    end
    X99Debugger.CopyBox.Clipboard:HighlightText()
    X99Debugger.CopyBox:Show()
  end
end

-- --------------------------------------------------------------------------------------------
-- Addon setup
-- --------------------------------------------------------------------------------------------
X99Debugger.Extended = false
X99Debugger.Mode = X99Console_Read
X99DebuggerConsoleScrollBar:SetScript("OnValueChanged", X99Debugger.ScrollBy)
X99DebuggerConsole:SetMaxLines(1000)
X99DebuggerConsole:SetFontObject(ChatFontNormal)
X99DebuggerConsole:SetFading(false)
X99DebuggerConsole:SetJustifyH("LEFT")
X99DebuggerConsole:ScrollByAmount(3)
X99DebuggerCopyClose:SetScript("OnClick", X99Debugger_ToggleConsole)