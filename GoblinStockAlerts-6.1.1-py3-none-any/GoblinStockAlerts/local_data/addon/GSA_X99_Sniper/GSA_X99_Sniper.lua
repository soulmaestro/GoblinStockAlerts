-- --------------------------------------------------------------------------------------------
-- Addon functions
-- --------------------------------------------------------------------------------------------
function GSA:LoadData()
  self:SetStatus(GSAStatus_LOADING)
  local realmID = GetRealmID()
  local realmName = GetRealmName()
  local connectedRealmID = GSARealms[realmID]
  local realmData = GSAData[connectedRealmID]
  GSARealmDisplay:SetText(realmName)
  X99Debugger:Print("Loading deals for connected realm " .. connectedRealmID .. "[Current realm: " .. realmName .. "(" .. realmID .. ")]", GSAYellow)

  if realmData == nil then
    self:ClearDisplay("No auctions found for this realm.", 1, 0, 0)
    self:SetStatus(GSAStatus_FINISHED)
  else
    self.tempList = GSAList:New()
    self.itemKeys = GSAList:New()

    self.deals = {}
    self.totalDeals = 0
    self.dealIndex = 0

    self.possibleDeals = GSAList:New()
    for _, deal in pairs(realmData) do
      local possibleDeal = {
        auctionID = deal["auction_id"],
        petID = deal["pet_id"],
        itemID = deal["item_id"],
        itemLevel = deal["item_level"],
        itemSuffix = deal["item_suffix"],
        wantedAmount = deal["quantity"] or 1
      }
      self.possibleDeals:Add(possibleDeal.auctionID, possibleDeal)
    end

    self:PreloadItems()
  end
end

function GSA:AddDeal(isCommodity, isPet, itemID, petID, auctionID, wantedAmount, availableAmount, unitPrice, totalPrice, itemLink)
  deal = {
    isCommodity = isCommodity,
    isPet = isPet,
    auctionID = auctionID,
    itemID = itemID,
    petID = petID,
    wantedAmount = wantedAmount,
    availableAmount = availableAmount,
    unitPrice = unitPrice,
    totalPrice = totalPrice,
    itemLink = itemLink
  }

  X99Debugger:Print("Adding new deal to the table", GSAGreen, X99Debugger_Extended)
  self.totalDeals = self.totalDeals + 1
  self.deals[self.totalDeals] = deal
  self:UpdateAuctionIndex()
  -- If we receive a new result after reaching the end
  if self.currentOperation == nil then
    GSA:Next(true)
  end
end

function GSA:PreloadItems()
  X99Debugger:Print("Preloading all items", GSACyan, X99Debugger_Extended)
  self:RegisterEvent("GET_ITEM_INFO_RECEIVED")

  for _, deal in pairs(self.possibleDeals.items) do
    -- Pets don't need to be cached
    if deal.itemID ~= nil then
      self.tempList:Add(deal.itemID, deal.itemID)
      if GetItemInfo(deal.itemID) == nil then
        X99Debugger:Print("Item " .. deal.itemID .. " is not cached.", GSAYellow, X99Debugger_Extended)
      else
        self.tempList:Remove(deal.itemID)
      end
    end
  end

  if self.tempList:Count() > 0 then
    self:SetStatus(GSAStatus_WAITING_FOR_ITEM_INFO)
    X99Debugger:Print("Waiting for item info", GSACyan, X99Debugger_Extended)
  else
    self:UnregisterEvent("GET_ITEM_INFO_RECEIVED")
    X99Debugger:Print("Ready for search", GSAGreen, X99Debugger_Extended)
    self:SetStatus(GSAStatus_READY)
  end
end

function GSA:UpdateItemInfo(itemID)
  -- If it is one of the items we are expecting
  if self.tempList:Has(itemID) then
    X99Debugger:Print("Received item info for " .. itemID, GSACyan, X99Debugger_Extended)
    self.tempList:Remove(itemID)
    if self.tempList:Count() == 0 then
      self.tempList:Clear()
      self:UnregisterEvent("GET_ITEM_INFO_RECEIVED")
      X99Debugger:Print("All items cached", GSAGreen)
      self:SetStatus(GSAStatus_READY)
    end
  end
end

function GSA:PrepareSearch()
  X99Debugger:Print("Preparing item keys", GSACyan, X99Debugger_Extended)
  self:RegisterEvent("ITEM_KEY_ITEM_INFO_RECEIVED")
  for _, deal in pairs(self.possibleDeals.items) do
    local itemKey

    -- Prepares the itemKey
    if deal.petID ~= nil then
      X99Debugger:Print("Creating item key for pet: " .. deal.petID, GSAYellow, X99Debugger_Extended)
      itemKey = C_AuctionHouse.MakeItemKey(82800, nil, nil, deal.petID)
      self.itemKeys:Add("pet:" .. tostring(deal.petID), itemKey, true)
    else
      X99Debugger:Print("Trying to get item level for " .. deal.itemID, GSAYellow, X99Debugger_Extended)
      local itemLevel
      if deal.itemLevel ~= nil then
        itemLevel = deal.itemLevel
      else
        itemLevel = GetItemLevel(deal.itemID)
      end

      X99Debugger:Print("Creating item key for item: " .. deal.itemID, GSAYellow, X99Debugger_Extended)
      itemKey = C_AuctionHouse.MakeItemKey(deal.itemID, itemLevel, deal.itemSuffix, nil)
      self.itemKeys:Add("item:" .. tostring(deal.itemID) .. ":" .. tostring(itemLevel) .. ":" .. tostring(deal.itemSuffix), itemKey)
    end

    deal.itemKey = itemKey
    local itemKeyInfo = C_AuctionHouse.GetItemKeyInfo(itemKey)
    if itemKeyInfo == nil then
      if deal.petID == nil then
        self.tempList:Add(deal.itemID)
      end
    end
  end

  if self.tempList:Count() > 0 then
    self:SetStatus(GSAStatus_WAITING_FOR_ITEM_KEY)
  else
    self:UnregisterEvent("ITEM_KEY_ITEM_INFO_RECEIVED")
    X99Debugger:Print("All items keys prepared", GSAGreen)
    self:SetStatus(GSAStatus_READY_FOR_SEARCH)
    self:SendSearch()
  end
end

function GSA:UpdateItemKey(itemID)
  X99Debugger:Print("Received item key for " .. itemID, GSAYellow, X99Debugger_Extended)
  -- If it is one of the items we are expecting
  if self.tempList:Has(itemID) then
    X99Debugger:Print("Received item key for " .. itemID, GSAYellow, X99Debugger_Extended)
    self.tempList:Remove(itemID)
    if self.tempList:Count() == 0 then
      self:UnregisterEvent("ITEM_KEY_ITEM_INFO_RECEIVED")
      X99Debugger:Print("All items keys prepared", GSAGreen)
      self:SetStatus(GSAStatus_READY_FOR_SEARCH)
    end
  end
end

function GSA:SendSearch()
  -- sort
  local sorts = { { sortOrder = Enum.AuctionHouseSortOrder.Buyout, reverseSort = false } }

  -- Executes the search
  local itemKey = self.itemKeys:Pop()
  C_AuctionHouse.SendSearchQuery(itemKey, sorts, true)
end

function GSA:SetStatus(status)
  X99Debugger:Print("Changing status to " .. status, nil, X99Debugger_Extended)
  self.status = status
  self:UpdateStatus()
end

function GSA:ProcessCommoditySearchResult(itemID)
  X99Debugger:Print("Receiving commodities search results", GSAYellow, X99Debugger_Extended)
  for i = 1, C_AuctionHouse.GetNumCommoditySearchResults(itemID) do
    local entry = C_AuctionHouse.GetCommoditySearchResultInfo(itemID, i)
    self:PrintCommodityAuction(entry)

    if self.possibleDeals:Has(entry.auctionID) then
      local possibleDeal = self.possibleDeals:Remove(entry.auctionID)
      self:AddDeal(
        true,
        false,
        possibleDeal.itemID,
              nil,
        possibleDeal.auctionID,
        possibleDeal.wantedAmount,
        entry.quantity,
        entry.unitPrice,
        entry.unitPrice * Min(entry.quantity, possibleDeal.wantedAmount),
        entry.itemID
      )
      X99Debugger:Print("Auction found and ready for purchase", GSAGreen)
    end
  end
end

function GSA:PrintCommodityAuction(entry)
  X99Debugger:Print("AuctionID: " .. entry.auctionID .. " ItemID: " .. entry.itemID .. " Quantity: " .. entry.quantity .. " Price " .. entry.unitPrice, nil, X99Debugger_Extended)
end

function GSA:ProcessItemSearchResult(itemKey)
  X99Debugger:Print("Receiving item search results", GSAYellow, X99Debugger_Extended)
  for i = 1, C_AuctionHouse.GetNumItemSearchResults(itemKey) do
    local entry = C_AuctionHouse.GetItemSearchResultInfo(itemKey, i)
    self:PrintItemAuction(entry)

    if self.possibleDeals:Has(entry.auctionID) then
      local possibleDeal = self.possibleDeals:Remove(entry.auctionID)
      self:AddDeal(
        false,
        itemKey.isPet,
        possibleDeal.itemID,
        possibleDeal.petID,
        possibleDeal.auctionID,
        possibleDeal.wantedAmount,
        entry.quantity,
        entry.buyoutAmount,
        entry.buyoutAmount,
        entry.itemLink
      )
      X99Debugger:Print("Auction found and ready for purchase: " .. entry.itemLink, GSAGreen)
    end
  end
end

function GSA:PrintItemAuction(entry)
  X99Debugger:Print("AuctionID: " .. entry.auctionID .. " ItemID: " .. entry.itemKey["itemID"] .. " Quantity: " .. entry.quantity .. " Price " .. entry.buyoutAmount, nil, X99Debugger_Extended)
end

function GSA:Next(skip)
  skip = skip or false

  if not skip then
    self.purchaseIndex = self.purchaseIndex + 1
    if self.purchaseIndex < self.currentOperation.wantedAmount then
      self:SetStatus(GSAStatus_READY_FOR_PURCHASE)
      return
    end
  end

  X99Debugger:Print("Moving to next auction.", GSAYellow)
  if self.dealIndex == self.totalDeals then
    self.currentOperation = nil
    self:ClearDisplay(nil, 1, 0, 0)
    self:SetStatus(GSAStatus_FINISHED)
  else
    self.dealIndex = self.dealIndex + 1
    self.currentOperation = self.deals[self.dealIndex]
    self.purchaseIndex = 0
    self:UpdateDisplay()
    self:UpdateAuctionIndex()
    self:SetStatus(GSAStatus_READY_FOR_PURCHASE)
  end
end

-- Buys an item
function GSA:BuyoutItem()
  if not self.Enabled then
    X99Debugger:Print("SLOW DOWN, we are not ready yet.", GSARed)
    return
  end

  self:SetStatus(GSAStatus_ITEM_PURCHASE_INITIALIZED)
  local money = GetMoney()
  if money >= self.currentOperation.unitPrice then
    C_AuctionHouse.PlaceBid(self.currentOperation.auctionID, self.currentOperation.unitPrice)
    self:SetStatus(GSAStatus_WAITING_ITEM_PURCHASE_CONFIRMATION)
  else
    X99Debugger:Print("Not enough money!", GSARed)
    self:Next("Not enough money!")
  end
end

-- Buy commodities
function GSA:InitiateCommoditiesPurchase()
  if not self.Enabled then
    X99Debugger:Print("SLOW DOWN, we are not ready yet.", GSARed)
    return
  end

  self:SetStatus(GSAStatus_COMMODITY_PURCHASE_INITIALIZED)
  local amount = Min(self.currentOperation.wantedAmount, GSA.currentOperation.availableAmount)
  local price = amount * self.currentOperation.unitPrice
  local money = GetMoney()
  GSA.currentOperation.amount = amount

  if money >= price then
    C_AuctionHouse.StartCommoditiesPurchase(self.currentOperation.itemID, amount)
  else
    X99Debugger:Print("Not enough money!", GSARed)
    self:Next("Not enough money!")
  end
end

function GSA:CompleteCommoditiesPurchase()
  C_AuctionHouse.ConfirmCommoditiesPurchase(self.currentOperation.itemID, GSA.currentOperation.amount)
  self:SetStatus(GSAStatus_WAITING_COMMODITY_PURCHASE_CONFIRMATION)
end

-- OnClick event handler for the Buy button
function OnBuy()
  if GSA.currentOperation.isCommodity then
    GSA:InitiateCommoditiesPurchase()
  else
    GSA:BuyoutItem()
  end
end

-- OnClick event handler for the Skip button
function OnSkip()
  GSA:Next(true)
end

-- Updates the main button status
function GSA:UpdateStatus()
  if self.status == GSAStatus_INITIALIZING then
    UpdateButton(GSAMainButton, false, false, "Initializing", nil)
    UpdateButton(GSASkipButton, false, false, "Initializing", nil)
  elseif self.status == GSAStatus_LOADING then
    UpdateButton(GSAMainButton, false, true, "Initializing", nil)
    UpdateButton(GSASkipButton, false, true, "Initializing", nil)
  elseif self.status == GSAStatus_WAITING_FOR_ITEM_INFO then
    UpdateButton(GSAMainButton, false, true, "Caching items", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_READY then
    UpdateButton(GSAMainButton, false, true, "Ready", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
    if self.Enabled then
      self:PrepareSearch()
    end
  elseif self.status == GSAStatus_WAITING_FOR_ITEM_KEY then
    UpdateButton(GSAMainButton, false, true, "Preparing keys", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_READY_FOR_SEARCH then
    UpdateButton(GSAMainButton, false, true, "Ready for search", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_SEARCH_INITIALIZED then
    UpdateButton(GSAMainButton, false, true, "Searching", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_WAITING_FOR_SEARCH_RESULTS then
    UpdateButton(GSAMainButton, false, true, "Searching", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_READY_FOR_PURCHASE then
    UpdateButton(GSAMainButton, true, true, "Buy", OnBuy)
    UpdateButton(GSASkipButton, true, true, "Skip", OnSkip)
  elseif self.status == GSAStatus_ITEM_PURCHASE_INITIALIZED then
    UpdateButton(GSAMainButton, false, true, "Buying", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_WAITING_ITEM_PURCHASE_CONFIRMATION then
    UpdateButton(GSAMainButton, false, true, "Buying", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_COMMODITY_PURCHASE_INITIALIZED then
    UpdateButton(GSAMainButton, false, true, "Buying", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_WAITING_COMMODITY_PURCHASE_CONFIRMATION then
    UpdateButton(GSAMainButton, false, true, "Buying", nil)
    UpdateButton(GSASkipButton, false, true, "Skip", nil)
  elseif self.status == GSAStatus_FINISHED then
    UpdateButton(GSAMainButton, false, false, "Done", nil)
    UpdateButton(GSASkipButton, false, false, "Done", nil)
  end
end

-- --------------------------------------------------------------------------------------------
-- Event callbacks
-- --------------------------------------------------------------------------------------------

function GSA:ITEM_SEARCH_RESULTS_UPDATED(_, itemKey)
  self:ProcessItemSearchResult(itemKey)
end

function GSA:COMMODITY_SEARCH_RESULTS_UPDATED(_, itemID)
  self:ProcessCommoditySearchResult(itemID)
end

function GSA:AUCTION_HOUSE_NEW_RESULTS_RECEIVED(_, itemKey)
  if X99Debugger.Extended then
    if itemKey == nil then
      return
    end
    itemKeyInfo = C_AuctionHouse.GetItemKeyInfo(itemKey)
    for key, value in pairs(itemKey) do
      X99Debugger:Print(key .. ":" .. value, GSAYellow)
    end
    for key, value in pairs(itemKeyInfo) do
      X99Debugger:Print(key .. ":" .. tostring(value), GSAYellow)
    end
  end
end

function GSA:ADDON_LOADED(_, addon)
  if addon == "GSA_X99_Sniper" then
    self:SetScript("OnShow", GSA.OnShow)
    self:SetScript("OnHide", GSA.OnClose)
    GSALocked = GSALocked or false
    self:SetScript("OnDragStart", GSA.StartMoving)
    self:SetScript("OnDragStop", GSA.StopMovingOrSizing)
    self:SetLocked(GSALocked)
    self.TitleText:SetText("X99 Sniper v1.1.1.1 (GSA " .. GSAVersion .. ")")

    local gender = UnitSex("player")
    if gender == 2 then
      self.portrait:SetTexture("Interface\\CHARACTERFRAME\\TemporaryPortrait-Male-Goblin")
    else
      self.portrait:SetTexture("Interface\\CHARACTERFRAME\\TemporaryPortrait-Female-Goblin")
    end

    FrameTemplate_SetButtonBarHeight(self, 30)
    GSADebugEnabled = GSADebugEnabled or false
    GSAExtendedDebug = GSAExtendedDebug or false
    GSADebugButton:HookScript("OnClick", GSAToggleDebug)
    GSADebugButton:SetChecked(GSADebugEnabled)

    X99Debugger:SetPoint("TOPLEFT", "GSA", "BOTTOMLEFT")
    X99Debugger:SetPoint("TOPRIGHT", "GSA", "BOTTOMRIGHT")
    X99Debugger.Extended = GSAExtendedDebug
    self:LoadData()
  end
end

function GSA:DisableAH()
  AuctionHouseFrameBuyTab:Hide()
  AuctionHouseFrameSellTab:Hide()
  AuctionHouseFrameAuctionsTab:Hide()
  AuctionHouseFrame.SearchBar:Hide()
end

function GSA:EnableAH()
  AuctionHouseFrameBuyTab:Show()
  AuctionHouseFrameSellTab:Show()
  AuctionHouseFrameAuctionsTab:Show()
  AuctionHouseFrame.SearchBar:Show()
end

function GSA:AUCTION_HOUSE_SHOW(_)
  self:Show()
end

function GSA:AUCTION_HOUSE_CLOSED(_)
  self:Hide()
end

function GSA:AUCTION_HOUSE_THROTTLED_SYSTEM_READY(_)
  if self.tempList:Count() == 0 and self.itemKeys:Count() > 0 then
    self:SendSearch()
  end

  if self.status == GSAStatus_COMMODITY_PURCHASE_INITIALIZED then
    self:CompleteCommoditiesPurchase()
    self:Next(true)
  elseif self.status == GSAStatus_WAITING_ITEM_PURCHASE_CONFIRMATION then
    self:Next()
  end
end

function GSA:GET_ITEM_INFO_RECEIVED(_, itemID)
  self:UpdateItemInfo(itemID)
end

function GSA:ITEM_KEY_ITEM_INFO_RECEIVED(_, itemID)
  self:UpdateItemKey(itemID)
end

-- --------------------------------------------------------------------------------------------
-- Addon initialization
-- --------------------------------------------------------------------------------------------

-- Event listener
function GSA:OnEvent(event, ...)
  X99Debugger:Print(event, GSAPurple, X99Debugger_Extended)
  if self[event] ~= nil then
    self[event](self, event, ...)
  end
end

function GSA:OnShow()
  -- self:DisableAH()
  self:RegisterEvents()
  self.Enabled = true
  if GSADebugEnabled then
    X99Debugger:Show()
  end
  if self.status == GSAStatus_READY then
    self:PrepareSearch()
  end
end

function GSA:OnClose()
  -- self.Enabled = false
  self:UnregisterEvents()
  X99Debugger:Hide()
  self:EnableAH()
end

function GSA:SetLocked(locked)
  if locked then
    self:RegisterForDrag()
  else
    self:RegisterForDrag("LeftButton")

  end
end

GSA:SetScript("OnEvent", GSA.OnEvent)

SLASH_GSA1 = "/gsa"
SlashCmdList.GSA = function(msg)
  if msg == "debug" then
    GSAExtendedDebug = not GSAExtendedDebug
    X99Debugger:SetExtendedMode(GSAExtendedDebug)
  elseif msg == "lock" then
    GSALocked = not GSALocked
    GSA:SetLocked(GSALocked)
  end
end