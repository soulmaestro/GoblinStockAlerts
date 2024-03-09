-- --------------------------------------------------------------------------------------------
-- Auction lists
-- --------------------------------------------------------------------------------------------
GSAList = {}

function GSAList:New()
  o = {
    items = {},
    size = 0
  }
  setmetatable(o, self)
  self.__index = self
  return o
end

function GSAList:Add(key, item)
  for k, _ in pairs(self.items) do
    if k == key then
      return
    end
  end
  self.items[key] = item
  self.size = self.size + 1
end

function GSAList:Has(key)
  return self.items[key] ~= nil
end

function GSAList:Get(key)
  return self.items[key]
end

function GSAList:Remove(key)
  local item = self:Get(key)
  self.items[key] = nil
  self.size = self.size - 1
  return item
end

function GSAList:Pop()
  local key
  for k, _ in pairs(self.items) do
    key = k
    break
  end
  return self:Remove(key)
end

function GSAList:Clear()
  self.items = {}
  self.size = 0
end

function GSAList:Count()
  return self.size
end

-- --------------------------------------------------------------------------------------------
-- Constants
-- --------------------------------------------------------------------------------------------

GSAStatus_INITIALIZING = 0
GSAStatus_LOADING = 1
GSAStatus_WAITING_FOR_ITEM_INFO = 2
GSAStatus_READY = 3
GSAStatus_WAITING_FOR_ITEM_KEY = 4
GSAStatus_READY_FOR_SEARCH = 5
GSAStatus_SEARCH_INITIALIZED = 6
GSAStatus_WAITING_FOR_SEARCH_RESULTS = 7
GSAStatus_READY_FOR_PURCHASE = 8
GSAStatus_ITEM_PURCHASE_INITIALIZED = 9
GSAStatus_WAITING_ITEM_PURCHASE_CONFIRMATION = 10
GSAStatus_COMMODITY_PURCHASE_INITIALIZED = 11
GSAStatus_WAITING_COMMODITY_PURCHASE_CONFIRMATION = 12
GSAStatus_FINISHED = 13

-- --------------------------------------------------------------------------------------------
-- Addon setup
-- --------------------------------------------------------------------------------------------

-- Main frame
GSA.Enabled = false
GSA.Status = GSAStatus_INITIALIZING

-- --------------------------------------------------------------------------------------------
-- Monitored events
-- --------------------------------------------------------------------------------------------

GSA:RegisterEvent("ADDON_LOADED")
GSA:RegisterEvent("AUCTION_HOUSE_SHOW")
GSA:RegisterEvent("AUCTION_HOUSE_CLOSED")

function GSA:RegisterEvents()
  self:RegisterEvent("ITEM_DATA_LOAD_RESULT")
  self:RegisterEvent("AUCTION_HOUSE_NEW_RESULTS_RECEIVED")
  self:RegisterEvent("ITEM_SEARCH_RESULTS_UPDATED")
  self:RegisterEvent("ITEM_PURCHASED")
  self:RegisterEvent("COMMODITY_SEARCH_RESULTS_UPDATED")
  self:RegisterEvent("COMMODITY_PURCHASED")
  self:RegisterEvent("COMMODITY_PURCHASE_SUCCEEDED")
  self:RegisterEvent("COMMODITY_PURCHASE_FAILED")
  self:RegisterEvent("AUCTION_HOUSE_BROWSE_FAILURE")
  self:RegisterEvent("AUCTION_HOUSE_THROTTLED_SYSTEM_READY")
  self:RegisterEvent("AUCTION_CANCELED")
end

function GSA:UnregisterEvents()
  self:UnregisterEvent("ITEM_DATA_LOAD_RESULT")
  self:UnregisterEvent("AUCTION_HOUSE_NEW_RESULTS_RECEIVED")
  self:UnregisterEvent("ITEM_SEARCH_RESULTS_UPDATED")
  self:UnregisterEvent("ITEM_PURCHASED")
  self:UnregisterEvent("COMMODITY_SEARCH_RESULTS_UPDATED")
  self:UnregisterEvent("COMMODITY_PURCHASED")
  self:UnregisterEvent("COMMODITY_PURCHASE_SUCCEEDED")
  self:UnregisterEvent("COMMODITY_PURCHASE_FAILED")
  self:UnregisterEvent("AUCTION_HOUSE_BROWSE_FAILURE")
  self:UnregisterEvent("AUCTION_HOUSE_THROTTLED_SYSTEM_READY")
  self:UnregisterEvent("AUCTION_CANCELED")
end

-- --------------------------------------------------------------------------------------------
-- Utility functions
-- --------------------------------------------------------------------------------------------

function GSAToggleDebug()
  GSADebugEnabled = GSADebugButton:GetChecked()
  if GSADebugEnabled then
    X99Debugger:Show()
  else
    X99Debugger:Hide()
  end
end

-- Get information about an item based on the itemID
function GetPetDisplayInfo(itemLink)
  local petSpeciesID, petLevel, petQuality = string.match(itemLink, "Hbattlepet:(%d+):(%d+):(%d+)")
  local speciesName, speciesIcon, _, _, _, _, _, _, _, _, _, _ = C_PetJournal.GetPetInfoBySpeciesID(petSpeciesID)
  return speciesName, tonumber(petQuality), speciesIcon, tonumber(petLevel)
end

-- Get information about a pet based on the petSpeciesID
function GetItemDisplayInfo(itemLink)
  local itemName, _, itemQuality, itemLevel, _, _, _, _, _, itemTexture , _, _, _, _, _, _, _ = GetItemInfo(itemLink)

  if not GSA.currentOperation.isCommodity then
    itemLevel = GetDetailedItemLevelInfo(itemLink)
  end

  return itemName, itemQuality, itemTexture, itemLevel
end

-- Get information about an item based on its id
function GetItemLevel(itemID)
  _, _, _, itemLevel, _, _, _, _, _, _, _, _, _, _, _, _ = GetItemInfo(itemID)
  return itemLevel
end

-- Quality color
function GetQualityColor(qualityID)
  if qualityID == 0 then
    return 0.62, 0.62, 0.62 -- Poor
  elseif qualityID == 1 then
    return 1.00, 1.00, 1.00 -- Common
  elseif qualityID == 2 then
    return 0.12, 1.00, 0.00 -- Uncommon
  elseif qualityID == 3 then
    return 0.00, 0.44, 0.87 -- Rare
  elseif qualityID == 4 then
    return 0.64, 0.21, 0.93 -- Epic
  elseif qualityID == 5 then
    return 1.00, 0.50, 0.00 -- Legendary
  elseif qualityID == 6 then
    return 0.90, 0.80, 0.50 -- Artifact
  elseif qualityID == 7 then
    return 0.00, 0.80, 1.00 -- Heirloon
  elseif qualityID == 8 then
    return 0.00, 0.80, 1.00 -- WoW Token
  end
end

-- Gets the minimun value
function Min(x, y)
  if x < y then
    return x
  else
    return y
  end
end

-- --------------------------------------------------------------------------------------------
-- Interface functions
-- --------------------------------------------------------------------------------------------

-- Updates current auction index
function GSA:UpdateAuctionIndex()
  GSAAuctionIndexDisplay:SetText("Deal " .. self.dealIndex .. " / " .. self.totalDeals)
end

-- Updates price and item
function GSA:UpdateDisplay()
  local name, quality, icon, itemLevel

  if self.currentOperation.petID ~= nil then
    name, quality, icon, itemLevel = GetPetDisplayInfo(self.currentOperation.itemLink)
  else
    name, quality, icon, itemLevel = GetItemDisplayInfo(self.currentOperation.itemLink)
  end

  if self.currentOperation.petID ~= nil then
    GSAItemName:SetText(name .. " (Level " .. tostring(itemLevel) .. ")")
  elseif (not self.currentOperation.isCommodity) and (itemLevel ~= nil) then
    GSAItemName:SetText(name .. " (iLvl " .. tostring(itemLevel) .. ")")
  else
    GSAItemName:SetText(name)
  end
  GSAItemName:SetTextColor(GetQualityColor(quality))
  GSAItemIcon:SetTexture(icon)

  GSAItemDesiredQuantity:SetText(self.currentOperation.wantedAmount)
  GSAItemDesiredQuantityLabel:Show()
  GSAItemDesiredQuantity:Show()

  GSAItemAvailable:SetText(self.currentOperation.availableAmount)
  GSAItemAvailableLabel:Show()
  GSAItemAvailable:Show()

  if not self.currentOperation.isCommodity then
    GSAItemPurchasedAmount:SetText(self.purchaseIndex .. "/" .. self.currentOperation.wantedAmount)
    GSAItemPurchasedAmountLabel:Show()
    GSAItemPurchasedAmount:Show()
  else
    GSAItemPurchasedAmount:SetText("")
    GSAItemPurchasedAmountLabel:Hide()
    GSAItemPurchasedAmount:Hide()
  end

  GSAItemPricePerUnit:SetText(GetCoinTextureString(self.currentOperation.unitPrice))
  GSAItemPricePerUnitLabel:Show()
  GSAItemPricePerUnit:Show()

  GSAItemTotalPrice:SetText(GetCoinTextureString(self.currentOperation.totalPrice))
  GSAItemTotalPriceLabel:Show()
  GSAItemTotalPrice:Show()
end

-- Clears the information
function GSA:ClearDisplay(message, r, g, b)
  GSAItemName:SetText(message)
  GSAItemName:SetTextColor(r, g, b)
  GSAItemIcon:SetTexture("")

  GSAItemDesiredQuantity:SetText("")
  GSAItemDesiredQuantityLabel: Hide()
  GSAItemDesiredQuantity: Hide()

  GSAItemAvailable:SetText("")
  GSAItemAvailableLabel:Hide()
  GSAItemAvailable:Hide()

  GSAItemPurchasedAmount:SetText("")
  GSAItemPurchasedAmountLabel:Hide()
  GSAItemPurchasedAmount:Hide()

  GSAItemPricePerUnit:SetText("")
  GSAItemPricePerUnitLabel:Hide()
  GSAItemPricePerUnit:Hide()

  GSAItemTotalPrice:SetText("")
  GSAItemTotalPriceLabel:Hide()
  GSAItemTotalPrice:Hide()
end

-- Updates the main button properties
function UpdateButton(button, enabled, visible, text, script)
  button:SetText(text)
  button:SetScript("OnClick", script)
  if enabled then
    button:Enable()
  else
    button:Disable()
  end

  if visible then
    button:Show()
  else
    button:Hide()
  end
end