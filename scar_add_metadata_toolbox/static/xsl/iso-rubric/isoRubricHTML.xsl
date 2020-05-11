<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:gco="http://www.isotc211.org/2005/gco" xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gml="http://www.opengis.net/gml" xmlns:gts="http://www.isotc211.org/2005/gts" xmlns:gmi="http://www.isotc211.org/2005/gmi" xmlns:srv="http://www.isotc211.org/2005/srv" xmlns:gmx="http://www.isotc211.org/2005/gmx" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink">
  <xd:doc xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl" scope="stylesheet">
    <xd:desc>
      <xd:p><xd:b>Updated on:</xd:b>Sept 15,2013</xd:p>
      <xd:p><xd:b>Created on:</xd:b>October 15, 2011</xd:p>
      <xd:p><xd:b>Author:</xd:b> ted.habermann@noaa.gov</xd:p>
    </xd:desc>
  </xd:doc>
  <!-- 9/15/2013 - anna.milan@noaa.gov: removed tests for extent @ids, added support for gmx:Anchor or gco:CharacterString for any element (element/*) -->
  <!-- 		July 27, 2012 - October 15, 2012: ted.habermann@noaa.gov		
    Did some work to adopt the rubric to service metadata:	Paths like //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation were changed to //gmd:identificationInfo//gmd:citation	in order to pick up titles for services in cases where no gmd:MD_DataIdentification exists.		Cleaned up and expanded the lineage paths to include embedded sources and process steps. Removed some unused variables: titleCnt, purposeCnt, some other *Cnt variables	-->
  <xsl:variable name="rubricVersion" select="'1.1.1'"/>
  <xsl:include href="./isoRubricStars.xsl"/>

  <xsl:template match="/">

    <!-- *************************************************************** -->
    <!-- calculation variables; must match variables isoRubricStars.xsl  -->
    <!-- *************************************************************** -->
    <!--       Metadata identifier      
      Spirals: ISOOptionalCore, CSWCoreQueryables, Identification    -->
    <xsl:variable name="idExist">
      <xsl:choose>
        <xsl:when test="(//gmd:fileIdentifier/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="idCnt" select="count(//gmd:fileIdentifier/*/text())"/>
    <!--       Metadata Contact      Spirals: ISOOptionalCore, CSWCoreQueryables, Identification    -->
    <xsl:variable name="metadataContactExist">
      <xsl:choose>
        <xsl:when test="(//gmd:contact/gmd:CI_ResponsibleParty)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="metadataContactCnt" select="count(//gmd:contact/gmd:CI_ResponsibleParty)"/>
    <xsl:variable name="metadataDateStampCnt" select="count(//gmd:dateStamp/gco:Date | //gmd:dateStamp/gco:DateTime)"/>
    <!-- 			The title from the first gmd:identificationInfo object is used. This could be gmd:MD_DataIdentification or srv:SV_ServiceIdentification			Spirals: ISOOCore, CSWCoreQueryables, Identification		-->
    <xsl:variable name="title" select="//gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:title/*/text()"/>
    <xsl:variable name="titleExist">
      <xsl:choose>
        <xsl:when test="string-length($title) &gt; 0">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <!--	    The resource date is indicated by a CI_DateTypeCode='creation, publication, or revision'. This could be gmd:MD_DataIdentification or srv:SV_ServiceIdentification.	    Spirals: Identification	  -->
    <xsl:variable name="resourceDateExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/*/text()                      or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/gco:DateTime                      or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:Date                      or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:DateTime                      or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='revision']/gmd:date/gco:Date                      or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='revision']/gmd:date/gco:DateTime)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <!--      The creation date is indicated by a CI_DateTypeCode='creation'. This could be gmd:MD_DataIdentification or srv:SV_ServiceIdentification.      Spirals: ISOMandatoryCore    -->
    <xsl:variable name="datasetLanguageCnt" select="count(//gmd:identificationInfo//gmd:language/*/text())"/>
    <xsl:variable name="creationDateExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/gco:Date                        or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/gco:DateTime                        or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:Date                        or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:DateTime                        or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='revision']/gmd:date/gco:Date                        or //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='revision']/gmd:date/gco:DateTime)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="topicCategoryCnt" select="count(//gmd:identificationInfo//gmd:topicCategory/gmd:MD_TopicCategoryCode)"/>
    <xsl:variable name="topicCategoryExist">
      <xsl:choose>
        <xsl:when test="count(//gmd:identificationInfo//gmd:topicCategory/gmd:MD_TopicCategoryCode)&gt;0">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <!-- The abstract could be gmd:MD_DataIdentification or srv:SV_ServiceIdentification.       Spirals: Identification, ISOMandatoryCore -->
    <xsl:variable name="abstractExist">
      <xsl:choose>
        <xsl:when test="count(//gmd:identificationInfo//gmd:abstract/*) &gt; 0">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="ISOMandatoryTotal" select="$titleExist + $creationDateExist + $datasetLanguageCnt + $topicCategoryExist + $abstractExist + $metadataContactExist + $metadataDateStampCnt"/>
    <xsl:variable name="ISOMandatoryMax">7</xsl:variable>
    <!-- ISO Conditional Core Fields: 4 possible -->
    <xsl:variable name="metadataLanguageCnt" select="count(gmi:MI_Metadata/gmd:language|gmd:MD_Metadata/gmd:language)"/>
    <xsl:variable name="metadataCharacterSetCnt" select="count(gmi:MI_Metadata/gmd:characterSet|gmd:MD_Metadata/gmd:characterSet)"/>
    <xsl:variable name="datasetCharacterSetCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:characterSet)"/>
    <xsl:variable name="resourceExtentExist">
      <xsl:choose>
        <xsl:when test="(((//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/*/text())     and (//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude/*/text())     and (//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude/*/text())     and (//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude/*/text()))     or ((//gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/*/text())     and (//gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude/*/text())     and (//gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude/*/text())     and (//gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude/*/text())))">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="ISOConditionalTotal" select="$metadataLanguageCnt + $metadataCharacterSetCnt + $datasetCharacterSetCnt + $resourceExtentExist"/>
    <xsl:variable name="ISOConditionalMax">4</xsl:variable>
    <!--  -->
    <!-- ISO Optional Core Fields: 12 possible -->
    <xsl:variable name="temporalExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent          or //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="temporalCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent          | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent)"/>
    <xsl:variable name="verticalExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent/gmd:minimumValue/gco:Real                     or //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent/gmd:minimumValue/gco:Real)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="verticalCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent/gmd:minimumValue/gco:Real                 | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent/gmd:minimumValue/gco:Real)"/>
    <xsl:variable name="resourceContactExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo//gmd:pointOfContact/gmd:CI_ResponsibleParty)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="resourceContactCnt" select="count(//gmd:identificationInfo//gmd:pointOfContact/gmd:CI_ResponsibleParty)"/>
    <xsl:variable name="lineageExist">
      <xsl:choose>
        <xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="lineageCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage)"/>
    <xsl:variable name="distOnlineResourceExist">
      <xsl:choose>
        <xsl:when test="(//gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL     | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="distOnlineResourceCnt" select="count(//gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL)"/>
    <xsl:variable name="onlineResourceURLExist">
      <xsl:choose>
        <xsl:when test="(//gmd:CI_OnlineResource/gmd:linkage/gmd:URL)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="onlineResourceURLCnt" select="count(//gmd:CI_OnlineResource/gmd:linkage/gmd:URL)"/>
    <xsl:variable name="onlineResourceNameExist">
      <xsl:choose>
        <xsl:when test="(//gmd:CI_OnlineResource/gmd:name/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="onlineResourceNameCnt" select="count(//gmd:CI_OnlineResource/gmd:name/*/text())"/>
    <xsl:variable name="allOnlineResourceNamesExist">
      <xsl:choose>
        <xsl:when test="$onlineResourceURLCnt and ($onlineResourceNameCnt = $onlineResourceURLCnt)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="onlineResourceDescExist">
      <xsl:choose>
        <xsl:when test="(//gmd:CI_OnlineResource/gmd:description/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="onlineResourceDescCnt" select="count(//gmd:CI_OnlineResource/gmd:description/*/text())"/>
    <xsl:variable name="allOnlineResourceDescExist">
      <xsl:choose>
        <xsl:when test="$onlineResourceURLCnt and ($onlineResourceDescCnt = $onlineResourceURLCnt)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="onlineResourceFunctionExist">
      <xsl:choose>
        <xsl:when test="(//gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="onlineResourceFunctionCnt" select="count(//gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode)"/>
    <xsl:variable name="allOnlineResourceFunctionExist">
      <xsl:choose>
        <xsl:when test="$onlineResourceURLCnt and ($onlineResourceFunctionCnt = $onlineResourceURLCnt)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="spatialRepresentationTypeCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType)"/>
    <xsl:variable name="distributionFormatExist">
      <xsl:choose>
        <xsl:when test="(//gmd:distributionInfo/gmd:MD_Distribution//gmd:MD_Format     | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:operationName/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="distributionFormatCnt" select="count(//gmd:distributionInfo//gmd:MD_Format | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:operationName/*/text())"/>
    <xsl:variable name="metadataStandardNameCnt" select="count(//gmd:metadataStandardName/*/text())"/>
    <xsl:variable name="metadataStandardVersionCnt" select="count(//gmd:metadataStandardVersion/*/text())"/>
    <xsl:variable name="referenceSystemCnt" select="count(gmi:MI_Metadata/gmd:referenceSystemInfo|gmd:MD_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem)"/>
    <xsl:variable name="spatialResolutionCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution)"/>
    <xsl:variable name="ISOOptionalTotal" select="$temporalExist + $verticalExist + $resourceContactExist + $lineageExist + $distOnlineResourceExist + $idExist + $spatialRepresentationTypeCnt  + $distributionFormatExist + $metadataStandardNameCnt + $metadataStandardVersionCnt     + $referenceSystemCnt + $spatialResolutionCnt"/>
    <xsl:variable name="ISOOptionalMax">12</xsl:variable>
    <xsl:variable name="ISOCoreTotal" select="$ISOMandatoryTotal + $ISOOptionalTotal + $ISOConditionalTotal"/>
    <xsl:variable name="ISOCoreMax" select="$ISOMandatoryMax + $ISOOptionalMax + $ISOConditionalMax"/>
    <!--  -->
    <xsl:variable name="datasetExtentDescriptionExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:description/*/text()          or //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:description/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="datasetExtentDescriptionCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:description/*/text()          | //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:description/*/text())"/>
    <!-- Keyword Type Fields -->
    <xsl:variable name="themeKeywordExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='theme']/gmd:keyword/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="themeKeywordCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='theme']/gmd:keyword/*/text())"/>
    <xsl:variable name="themeKeywordThesaurusExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='theme']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="themeKeywordThesaurusCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='theme']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())"/>
    <!--  -->
    <xsl:variable name="dataCenterKeywordExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='dataCenter']/gmd:keyword/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="dataCenterKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='dataCenter'])"/>
    <xsl:variable name="dataCenterKeywordThesaurusExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='dataCenter']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="dataCenterKeywordThesaurusCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='dataCenter']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())"/>
    <!--  -->
    <xsl:variable name="projectKeywordExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='project']/gmd:keyword/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="projectKeywordCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='project']/gmd:keyword/*/text())"/>
    <xsl:variable name="projectKeywordThesaurusExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='project']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="projectKeywordThesaurusCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='project']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())"/>
    <!--  -->
    <xsl:variable name="placeKeywordExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='place']/gmd:keyword/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="placeKeywordCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='place']/gmd:keyword/*/text())"/>
    <xsl:variable name="placeKeywordThesaurusExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='place']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="placeKeywordThesaurusCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='place']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())"/>
    <!--  -->
    <xsl:variable name="instrumentKeywordExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='instrument']/gmd:keyword/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="instrumentKeywordCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='instrument']/gmd:keyword/*/text())"/>
    <xsl:variable name="instrumentKeywordThesaurusExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='instrument']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="instrumentKeywordThesaurusCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='instrument']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())"/>
    <!--  -->
    <xsl:variable name="platformKeywordExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='platform']/gmd:keyword/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="platformKeywordCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='platform']/gmd:keyword/*/text())"/>
    <xsl:variable name="platformKeywordThesaurusExist">
      <xsl:choose>
        <xsl:when test="//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='platform']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text()">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="platformKeywordThesaurusCnt" select="count(//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='platform']/gmd:thesaurusName/gmd:CI_Citation/gmd:title/*/text())"/>
    <!-- Distribution Spiral Scores -->
    <xsl:variable name="distributorContactExist">
      <xsl:choose>
        <xsl:when test="(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact/gmd:CI_ResponsibleParty     | //gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="distributorContactCnt" select="count(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact/gmd:CI_ResponsibleParty   | //gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty)"/>
    <xsl:variable name="graphicOverviewCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/*/text())"/>
    <xsl:variable name="graphicOverviewExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <!-- Description Scores -->
    <xsl:variable name="purposeExist">
      <xsl:choose>
        <xsl:when test="(//gmd:identificationInfo//gmd:purpose/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="lineageStatementExist">
      <xsl:choose>
        <xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="lineageStatementCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/*/text())"/>
    <!-- Content Information Scores -->
    <xsl:variable name="contentTypeExist">
      <xsl:choose>
        <xsl:when test="(//gmd:contentInfo//gmd:contentType/gmd:MD_CoverageContentTypeCode)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="contentTypeCnt" select="count(//gmd:contentInfo//gmd:contentType/gmd:MD_CoverageContentTypeCode)"/>
    <xsl:variable name="dimensionNameExist">
      <xsl:choose>
        <xsl:when test="(//gmd:contentInfo//gmd:dimension//gmd:sequenceIdentifier/gco:MemberName/gco:aName)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="dimensionNameCnt" select="count(//gmd:contentInfo//gmd:dimension//gmd:sequenceIdentifier/gco:MemberName/gco:aName)"/>
    <xsl:variable name="dimensionDescriptorExist">
      <xsl:choose>
        <xsl:when test="(//gmd:contentInfo//gmd:dimension//gmd:descriptor/*/text())">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="dimensionDescriptorCnt" select="count(//gmd:contentInfo//gmd:dimension//gmd:descriptor/*/text())"/>
    <xsl:variable name="dimensionUnitsExist">
      <xsl:choose>
        <xsl:when test="(//gmd:contentInfo//gmd:dimension//gmd:units)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="dimensionUnitsCnt" select="count(//gmd:contentInfo//gmd:dimension//gmd:units)"/>
    <!-- Lineage Scores -->
    <xsl:variable name="sourceExist">
      <xsl:choose>
        <xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source           | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmi:LE_Source          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep//gmd:source/gmi:LE_Source          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep//gmd:source/gmd:LI_Source)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sourceCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source           | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmi:LE_Source          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep//gmd:source/gmi:LE_Source          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep//gmd:source/gmd:LI_Source)"/>
    <xsl:variable name="processStepExist">
      <xsl:choose>
        <xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LI_ProcessStep          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmi:LE_ProcessStep          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source//gmd:sourceStep/gmd:LI_ProcessStep          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source//gmd:sourceStep/gmi:LE_ProcessStep)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="processStepCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LI_ProcessStep          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmi:LE_ProcessStep          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source//gmd:sourceStep/gmd:LI_ProcessStep          | //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source//gmd:sourceStep/gmi:LE_ProcessStep)"/>
    <!-- Acquisition Information Scores -->
    <xsl:variable name="instrumentExist">
      <xsl:choose>
        <xsl:when test="(/gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:instrument/gmi:MI_Instrument | /gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform/gmi:instrument/gmi:MI_Instrument)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="instrumentCnt" select="count(/gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:instrument/gmi:MI_Instrument | /gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform/gmi:instrument/gmi:MI_Instrument)"/>
    <xsl:variable name="platformExist">
      <xsl:choose>
        <xsl:when test="(/gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform)">1</xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="platformCnt" select="count(/gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform)"/>
    <!-- Spiral Scores -->
    <xsl:variable name="identificationTotal" select="$idExist + $titleExist  + $abstractExist + $resourceDateExist + $topicCategoryExist + $themeKeywordExist + $themeKeywordThesaurusExist + $metadataContactExist + $resourceContactExist"/>
    <xsl:variable name="identificationMax">9</xsl:variable>
    <xsl:variable name="identificationColumn">
      <xsl:choose>
        <xsl:when test="$identificationTotal=0">0</xsl:when>
        <xsl:when test="$identificationTotal=$identificationMax">4</xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="floor(number(number($identificationTotal) * 3 div number($identificationMax)))"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="extentTotal" select="$resourceExtentExist + $temporalExist  + $verticalExist + $placeKeywordExist + $placeKeywordThesaurusExist"/>
    <xsl:variable name="extentMax">5</xsl:variable>
    <xsl:variable name="connectionTotal" select="$onlineResourceURLExist + $allOnlineResourceNamesExist + $allOnlineResourceDescExist + $allOnlineResourceFunctionExist"/>
    <xsl:variable name="connectionMax">4</xsl:variable>
    <xsl:variable name="distributionTotal" select="$distributorContactExist + $distributionFormatExist + $distOnlineResourceExist + $graphicOverviewExist + $dataCenterKeywordExist + $dataCenterKeywordThesaurusExist"/>
    <xsl:variable name="distributionMax">6</xsl:variable>
    <xsl:variable name="contentTotal" select="$contentTypeExist + $dimensionDescriptorExist + $dimensionNameExist + $dimensionUnitsExist"/>
    <xsl:variable name="contentMax">4</xsl:variable>
    <xsl:variable name="descriptionTotal" select="$datasetExtentDescriptionExist + $purposeExist + $lineageStatementExist + $projectKeywordExist + $projectKeywordThesaurusExist"/>
    <xsl:variable name="descriptionMax">5</xsl:variable>
    <xsl:variable name="lineageTotal" select="$sourceExist + $processStepExist"/>
    <xsl:variable name="lineageMax">2</xsl:variable>
    <xsl:variable name="acquisitionTotal" select="$instrumentExist + $platformExist + $instrumentKeywordExist + $instrumentKeywordThesaurusExist + $platformKeywordExist + $platformKeywordThesaurusExist"/>
    <xsl:variable name="acquisitionMax">6</xsl:variable>
    <xsl:variable name="spiralTotal" select="$identificationTotal + $extentTotal + $connectionTotal + $distributionTotal + $descriptionTotal + $lineageTotal + $acquisitionTotal + $contentTotal"/>
    <xsl:variable name="spiralMax" select="$identificationMax + $extentMax + $connectionMax + $distributionMax + $descriptionMax + $lineageMax + $acquisitionMax + $contentMax"/>
    <!-- *************** -->
    <html>
      <head>
        <style type="text/css">
          .sprite{
              display:-moz-inline-box;
              display:inline-block;
              margin:0;
              padding:0;
              overflow:hidden;
              vertical-align:middle;
              background:url(http://g-ecx.images-amazon.com/images/G/01/common/sprites/sprite-site-wide-2._V234302190_.png) no-repeat;
          }
          .star_0_0{
              background-position:-95px 0px;
              width:52px;
              height:13px;
          }
          .star_0_5{
              background-position:-82px -20px;
              width:52px;
              height:13px;
          }
          .star_1_0{
              background-position:-82px 0px;
              width:52px;
              height:13px;
          }
          .star_1_5{
              background-position:-69px -20px;
              width:52px;
              height:13px;
          }
          .star_2_0{
              background-position:-69px 0px;
              width:52px;
              height:13px;
          }
          .star_2_5{
              background-position:-56px -20px;
              width:52px;
              height:13px;
          }
          .star_3_0{
              background-position:-56px 0px;
              width:52px;
              height:13px;
          }
          .star_3_5{
              background-position:-43px -20px;
              width:52px;
              height:13px;
          }
          .star_4_0{
              background-position:-43px 0px;
              width:52px;
              height:13px;
          }
          .star_4_5{
              background-position:-30px -20px;
              width:52px;
              height:13px;
          }
          .star_5_0{
              background-position:-30px 0px;
              width:52px;
              height:13px;
          }</style>
      </head>
      <body>
        <!-- Links to Alternate ISO views -->
        <h1>ISO 19115 SpiralTracker Report</h1>
        <p>This report identifies ISO metadata elements described in spirals of documentation development described in <a href="https://geo-ide.noaa.gov/wiki/index.php?title=Creating_Good_Documentation">Creating Good Documentation</a>. Together these spirals build a strong foundation for high-quality documentation. The ISO Standard includes a number of options for building on that foundation by addressing specific scientific needs. See <a href="https://geo-ide.noaa.gov/wiki/index.php?title=Use_Cases_to_CRUD">Use Cases to CRUD</a> for some examples. </p>
        <p>The elements are listed by name and are followed by M, C, or O if they are Mandatory, Conditional or Optional. They are followed by UDD (attribute name) if they are included in the <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">NetCDF Attribute Convention for Dataset Discovery</a>.</p>
        <p>The ISO 19115 Standard recommends <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">Core Elements</a> for inclusion in metadata. This tool tests also conformance with those recommendations.</p>
        <p>The Rubric at the top of the report summarizes the results. Each spiral is represented by a row in the rubric. The columns show the % of the elements in that spiral that exist in the record. Click the spiral name for more details.</p>
        <p>This report is produced using this <a href="https://www.ngdc.noaa.gov/metadata/published/xsl/isoRubricHTML.xsl">stylesheet</a>. Please contact <a href="mailto:ngdc.metadata-support@noaa.gov">metadata support</a> if you have questions or suggestions.</p>
        <p>The tables included below include <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_xPaths">xPaths</a> that give the locations of the elements included in the rubric in the ISO XML schema.</p>
        <h2> Title: <xsl:value-of select="$title"/></h2>
        <a name="Total Spiral"/>
        <h2>Total Spiral Score: <xsl:value-of select="$spiralTotal"/>/<xsl:value-of select="$spiralMax"/></h2>
        <style type="text/css">
          table{
              empty-cells:show;
          }</style>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader">Spiral</th>
            <th class="reportHeader">None <span class="sprite star_0_0"/></th>
            <th class="reportHeader">1-33% <span class="sprite star_1_0"/></th>
            <th class="reportHeader">34-66% <span class="sprite star_2_0"/></th>
            <th class="reportHeader">67-99% <span class="sprite star_3_0"/></th>
            <th class="reportHeader">All <span class="sprite star_4_0"/></th>
          </tr>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Total Spiral'"/>
            <xsl:with-param name="total" select="$spiralTotal"/>
            <xsl:with-param name="max" select="$spiralMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Identification'"/>
            <xsl:with-param name="total" select="$identificationTotal"/>
            <xsl:with-param name="max" select="$identificationMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Connection'"/>
            <xsl:with-param name="total" select="number($connectionTotal)"/>
            <xsl:with-param name="max" select="number($connectionMax)"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Extent'"/>
            <xsl:with-param name="total" select="$extentTotal"/>
            <xsl:with-param name="max" select="$extentMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Distribution'"/>
            <xsl:with-param name="total" select="$distributionTotal"/>
            <xsl:with-param name="max" select="$distributionMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Description'"/>
            <xsl:with-param name="total" select="$descriptionTotal"/>
            <xsl:with-param name="max" select="$descriptionMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Content'"/>
            <xsl:with-param name="total" select="$contentTotal"/>
            <xsl:with-param name="max" select="$contentMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Lineage'"/>
            <xsl:with-param name="total" select="$lineageTotal"/>
            <xsl:with-param name="max" select="$lineageMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Acquisition Information'"/>
            <xsl:with-param name="total" select="$acquisitionTotal"/>
            <xsl:with-param name="max" select="$acquisitionMax"/>
          </xsl:call-template>
        </table>
        <h2>Total ISO Core Score: <xsl:value-of select="$ISOCoreTotal"/>/<xsl:value-of select="$ISOCoreMax"/></h2>
        <p>Note: The Total ISO Core Score does not count toward the Total Spiral Score</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader">Spiral</th>
            <th class="reportHeader">None</th>
            <th class="reportHeader">1-33%</th>
            <th class="reportHeader">34-66%</th>
            <th class="reportHeader">67-99%</th>
            <th class="reportHeader">All</th>
          </tr>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'Total Core Score'"/>
            <xsl:with-param name="total" select="$ISOCoreTotal"/>
            <xsl:with-param name="max" select="$ISOCoreMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'ISO Core Mandatory'"/>
            <xsl:with-param name="total" select="$ISOMandatoryTotal"/>
            <xsl:with-param name="max" select="$ISOMandatoryMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'ISO Core Conditional'"/>
            <xsl:with-param name="total" select="$ISOConditionalTotal"/>
            <xsl:with-param name="max" select="$ISOConditionalMax"/>
          </xsl:call-template>
          <xsl:call-template name="showColumn">
            <xsl:with-param name="name" select="'ISO Core Optional'"/>
            <xsl:with-param name="total" select="$ISOOptionalTotal"/>
            <xsl:with-param name="max" select="$ISOOptionalMax"/>
          </xsl:call-template>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Identification"/>
        <h2>Identification Score: <xsl:value-of select="$identificationTotal"/>/<xsl:value-of select="$identificationMax"/></h2>
        <p>The Identification Spiral sets the stage for discovery using text search engines. It includes a unique identifier for the metadata, a title, an abstract, theme keywords and contact information for the metadata and the dataset.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$idExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Identifier<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (id)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">A unique phrase or string which uniquely identifies the metadata file.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Each metadata record shall include a character string as a unique identifier. There are two general approaches to ensuring uniqueness for these identifiers:<br/> 1. use a universal unique identifier (<a href="http://en.wikipedia.org/wiki/Universally_Unique_Identifier">UUID</a>), to distinguish it from other resources.<br/> 2. Include a namespace and a code guarenteed to be unique in that namespace in the identifier. For example: <br/>
gov.noaa.class:AERO100<br/> In this case gov.noaa.class is a namespace and AERO100 is a code guaranteed to be unique in that namespace.<br/> It seems likely that the upcoming revision of ISO 19115 will support MD_Identifiers as metadata identifiers. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Identifiers">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top"> //gmd:fileidentifier</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$titleExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Title<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (title)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Name by which the resource is known</td>
            <td class="reportRowHeading" valign="top">
              <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Identification_Information">More...</a>
            </td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:title</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$resourceDateExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Date<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (title)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Date associated with the resource (publication/creation/revision).</td>
            <td class="reportRowHeading" valign="top">Whenever possible, include both creation date and revision date. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Dates">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode='creation']/gmd:date/gco:Date <br/>or<br/> //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode='creation']/gmd:date/gco:DateTime <br/>or<br/> //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode='publication']/gmd:date/gco:Date <br/>or<br/> //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode='publication']/gmd:date/gco:DateTime <br/>or<br/> //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode='revision']/gmd:date/gco:Date <br/>or<br/> //gmd:identificationInfo//gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode='revision']/gmd:date/gco:DateTime</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$abstractExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Abstract<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (summary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Brief narrative summary of the resource contents.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Abstract narrative should include information on general content and features; dataset application: GIS, CAD, image, database; geographic coverage: county/city name; time period of content: begin and end date or single date; and special data characteristics or limitations. Note: Many applications limit preliminary display to the first 150-200 characters of this field so critical distinguishing characteristics should be listed first. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Identification_Information">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:abstract</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$topicCategoryExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Topic Category (<xsl:value-of select="$topicCategoryCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The main theme(s) of the dataset.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Select topicCategory from MD_TopicCategoryCode. Usually climatologyMeteorologyAtmosphere and/or oceans (keep this capitalization and spacing).</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$themeKeywordExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Theme Keywords (<xsl:value-of select="$themeKeywordCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Keywords that describe the general theme of the resource.</td>
            <td class="reportRowHeading" valign="top" rowspan="2">The <a href="http://gcmd.nasa.gov/learn/keyword_list.html">NASA Global Change Master Directory</a> and the <a href="http://cf-pcmdi.llnl.gov/documents/cf-standard-names/">Climate-Forecast Standard Names</a> are good choices for keyword thesaurus.<p>In order to be identified by SpiralTracker, the keyword must have MD_KeywordTypeCode = theme</p></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='theme']/gmd:keyword</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$themeKeywordThesaurusExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Theme Keyword Thesaurus (<xsl:value-of select="$themeKeywordThesaurusCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords_vocabulary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of a registered authoritative keyword resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='theme']/gmd:thesaurusName/gmd:CI_Citation/gmd:title</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataContactExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Contact<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (creator_name, URL, email)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The responsible party for the metadata content.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The person/organization directly responsible for metadata creation and maintenance.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:contact/gmd:CI_ResponsibleParty</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$resourceContactExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Contact (<xsl:value-of select="$resourceContactCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (creator_name, URL, email)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Identification and means to contact people/organizations associated with the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The person/organization directly responsible for answering questions about a resource. This could be a person at an archive rather than the originator of the resource (described in the citation).</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:pointOfContact/gmd:CI_ResponsibleParty</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Extent"/>
        <h2>Extent Score: <xsl:value-of select="$extentTotal"/>/<xsl:value-of select="$extentMax"/></h2>
        <p>The Extent Spiral defines the spatial and temporal extent of the dataset. This information can be displayed on maps and timelines and used in spatial searches. The ISO standard supports the definition of multiple extents for each dataset. In order to simplify the process of identifying the bounding extent, it is recommended that the id attribute be set = "boundingExtent". </p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$resourceExtentExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Spatial Extent<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">C</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (geospatial_lat_min max, geospatial_lon_min max)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Describes the spatial, horizontal and/or vertical, and the temporal coverage in the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The bounding extent for the resource should be identified with id="boundingExtent": &lt;gmd:EX_Extent id="boundingExtent"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents"> More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude
              <br/>and<br/>              //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude 
              <br/>and<br/>              //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude 
              <br/>and<br/>              //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude 
              <br/>or<br/>              //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude 
              <br/>and<br/>              //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude 
              <br/>and<br/>              //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude 
              <br/>and<br/>            //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$temporalExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Temporal Extent<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (time_coverage_start end)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Describes the temporal coverage in the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">A temporal element could be used to describe either the time period covered by the content of the dataset (e.g. during the Jurassic) or the date and time when the data has been collected (e.g. the date on which the geological study was completed). If both are needed, then two temporal extents should be provided. The use of multiple temporal extents should be explained in the attribute description of the extent. The bounding extent for the resource should be identified with id="boundingExtent": &lt;gmd:EX_Extent id="boundingExtent"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent <br/>or<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$verticalExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Vertical Extent</td>
            <td class="reportRowHeading" colspan="1" valign="top">The elements which give the minimum and maximum of the vertical extent of the dataset.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The bounding extent for the resource should be identified with id="boundingExtent": &lt;gmd:EX_Extent id="boundingExtent"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent <br/>or<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$placeKeywordExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Place Keywords (<xsl:value-of select="$placeKeywordCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Keywords that describe the location of the resource.</td>
            <td class="reportRowHeading" valign="top" rowspan="2">The <a href="http://gcmd.nasa.gov/learn/keyword_list.html">NASA Global Change Master Directory</a> is a good choice for keyword thesaurus.<p>In order to be identified by SpiralTracker, the keyword must have MD_KeywordTypeCode = place</p></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='place']/gmd:keyword</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$placeKeywordThesaurusExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Place Keyword Thesaurus (<xsl:value-of select="$placeKeywordThesaurusCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords_vocabulary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of a registered authoritative keyword resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='place']/gmd:thesaurusName/gmd:CI_Citation/gmd:title</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Connection"/>
        <h2>Connection Score: <xsl:value-of select="$connectionTotal"/>/<xsl:value-of select="$connectionMax"/></h2>
        <p>The ISO Standards for describing onlineResources make it possible to display meaningful titles and descriptions for URLs. This spiral checks that all of the URL names, descriptions, and functions exist.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$onlineResourceURLExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Online Resource URLs (<xsl:value-of select="$onlineResourceURLCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">URLs for online resources.</td>
            <td class="reportRowHeading" colspan="1" valign="top" rowspan="4">Information for Online Resources <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Online_Resources">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:CI_OnlineResource/gmd:linkage/gmd:URL</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$allOnlineResourceFunctionExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Online Resource Functions (<xsl:value-of select="$onlineResourceFunctionCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Function code for online resources. Valids include: download, information, offlineAccess, order, search</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$allOnlineResourceNamesExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Online Resource Names (<xsl:value-of select="$onlineResourceNameCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Title for online resources, usually displayed as the link.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:CI_OnlineResource/gmd:name</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$allOnlineResourceDescExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Online Resource Description (<xsl:value-of select="$onlineResourceDescCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">A short paragraph describing an online resource, usually displayed with a link.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:CI_OnlineResource/gmd:description</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Distribution"/>
        <h2>Distribution/Services Score: <xsl:value-of select="$distributionTotal"/>/<xsl:value-of select="$distributionMax"/></h2>
        <p>Discovering that a dataset exists is not helpful unless you can also discover where the dataset is available from. The Distribution Spiral provides that information.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$distributorContactExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Distributor Contact (<xsl:value-of select="$distributorContactCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">The contact for distribution of the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The organization directly responsible for distribution of the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact <br/> or //gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$distOnlineResourceExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Online Resource (<xsl:value-of select="$distOnlineResourceCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Information about Internet hosted resources: availability; URL; protocol used; resource name; resource description, and resource function.</td>
            <td class="reportRowHeading" colspan="1" valign="top">
              <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Online_Resources">More...</a>
            </td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL <br/>or<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$distributionFormatExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Distribution Format (<xsl:value-of select="$distributionFormatCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Description of distribution format.</td>
            <td class="reportRowHeading" colspan="1" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat/gmd:MD_Format <br/>or<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:operationName</td>
          </tr>
          <tr>x <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$dataCenterKeywordExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Data Center Keywords (<xsl:value-of select="$dataCenterKeywordCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Keywords that describe a Data Center related to the resource.</td>
            <td class="reportRowHeading" valign="top" rowspan="2">The <a href="http://gcmd.nasa.gov/learn/keyword_list.html">NASA Global Change Master Directory</a> is a good choice for keyword thesaurus. <p>In order to be identified by SpiralTracker, the keyword must have MD_KeywordTypeCode = dataCenter</p></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='dataCenter']/gmd:keyword</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$dataCenterKeywordThesaurusExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Data Center Keyword Thesaurus (<xsl:value-of select="$dataCenterKeywordThesaurusCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords_vocabulary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of a registered authoritative keyword resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/*gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='dataCenter']/gmd:thesaurusName/gmd:CI_Citation/gmd:title</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$graphicOverviewExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Browse Graphic (<xsl:value-of select="$graphicOverviewCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of, description of, and file type of an illustration of the dataset.</td>
            <td class="reportRowHeading"/>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Description"/>
        <h2>Description Score: <xsl:value-of select="$descriptionTotal"/>/<xsl:value-of select="$descriptionMax"/></h2>
        <p>The Description Spiral provides additional information that may be searched in some text searches. It includes brief textural descriptions of items that are also described quantitatively in other spirals.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$purposeExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Purpose</td>
            <td class="reportRowHeading" colspan="1" valign="top">Summary of the intentions for which the dataset was developed.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Purpose includes objectives for creating the dataset and what the dataset is to support.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:purpose</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$datasetExtentDescriptionExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Extent Description</td>
            <td class="reportRowHeading" colspan="1" valign="top">Text which describes the spatial and temporal extent of the dataset.</td>
            <td class="reportRowHeading" valign="top">When referring to a named location this can be also listed as a keyword with type = "place". <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:description</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$lineageStatementExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Lineage Statement<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (history)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">General explanation of the data producer's knowledge of the resource sources and processing.</td>
            <td class="reportRowHeading" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$projectKeywordExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Project Keywords (<xsl:value-of select="$projectKeywordCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Keywords that describe a Project related to the resource.</td>
            <td class="reportRowHeading" valign="top" rowspan="2">The <a href="http://gcmd.nasa.gov/learn/keyword_list.html">NASA Global Change Master Directory</a> is a good choice for keyword thesaurus. <p>In order to be identified by SpiralTracker, the keyword must have MD_KeywordTypeCode = project</p></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='project']/gmd:keyword</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$projectKeywordThesaurusExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Project Keyword Thesaurus (<xsl:value-of select="$projectKeywordThesaurusCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords_vocabulary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of a registered authoritative keyword resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:type/gmd:MD_KeywordTypeCode/@codeListValue='project']/gmd:thesaurusName/gmd:CI_Citation/gmd:title</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Content"/>
        <h2>Content Score: <xsl:value-of select="$contentTotal"/>/<xsl:value-of select="$contentMax"/></h2>
        <p>The Content Spiral includes information about the parameters that are included in a dataset.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$contentTypeExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Content Type (<xsl:value-of select="$contentTypeCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Type of the content in the cell.</td>
            <td class="reportRowHeading" valign="top">Select contentType from MD_CoverageContentTypeCode. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=Coverages_and_ISO_Metadata">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:contentInfo//gmd:contentType/gmd:MD_CoverageContentTypeCode</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$dimensionNameExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Band Name (<xsl:value-of select="$dimensionNameCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Name of the parameter in the band.</td>
            <td class="reportRowHeading" valign="top">This name must uniquely identify a parameter in the attributeDescription. The <a href="http://cf-pcmdi.llnl.gov/documents/cf-standard-names/">Climate-Forecast Standard Names</a> are conventional choices for attribute names.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:contentInfo//gmd:dimension//gmd:sequenceIdentifier/gco:MemberName/gco:aName</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$dimensionDescriptorExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Band Definition (<xsl:value-of select="$dimensionDescriptorCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Definition of the parameter in the band.</td>
            <td class="reportRowHeading" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:contentInfo//gmd:dimension//gmd:descriptor</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$dimensionUnitsExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Band Units (<xsl:value-of select="$dimensionUnitsCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Units of the parameter in the band. </td>
            <td class="reportRowHeading" valign="top">The Unidata <a href="http://www.unidata.ucar.edu/software/udunits/">UDUNITS</a> is a source of standard unit names.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:contentInfo//gmd:dimension//gmd:units</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Lineage"/>
        <h2>Lineage Score: <xsl:value-of select="$lineageTotal"/>/<xsl:value-of select="$lineageMax"/></h2>
        <p>The Lineage Spiral begins the description of how the data have been measured and processed.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$sourceExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Source (<xsl:value-of select="$sourceCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Information on the sources used in the development of the dataset.</td>
            <td class="reportRowHeading" rowspan="2" valign="top">Using xml ids for sources and processSteps makes it possible to refer to them from one another: &lt;gmd:LI_Source id="src_AVHRR_GAC.1074123.65352"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Lineage">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source <br/>or<br/> //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmi:LE_Source <br/>or<br/> //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep//gmd:source/gmi:LE_Source <br/>or<br/> //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep//gmd:source/gmd:LI_Source</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$processStepExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Process Step (<xsl:value-of select="$processStepCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (history)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The events in the development of the dataset. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Lineage">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LI_ProcessStep <br/>or<br/> //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmi:LE_ProcessStep <br/>or<br/> //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source//gmd:sourceStep/gmd:LI_ProcessStep <br/>or<br/> //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source//gmd:sourceStep/gmi:LE_ProcessStep</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="Acquisition Information"/>
        <h2>Acquisition Information Score: <xsl:value-of select="$acquisitionTotal"/>/<xsl:value-of select="$acquisitionMax"/></h2>
        <p>The Acquisition Information Spiral provides information about instruments used to make observations and platforms that they are mounted on.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$instrumentExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Instrument (<xsl:value-of select="$instrumentCnt"/>)<br/></td>
            <td class="reportRowHeading">Information about the instrument used to make the observations.</td>
            <td class="reportRowHeading" colspan="1" valign="top">
              <a href="https://geo-ide.noaa.gov/wiki/index.php?title=Instruments">More...</a>
            </td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:instrument/gmi:MI_Instrument <br/>or<br/> /gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform/gmi:instrument/gmi:MI_Instrument </td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$platformExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Platform (<xsl:value-of select="$platformCnt"/>)<br/></td>
            <td class="reportRowHeading" colspan="1" valign="top">The platform used to collect the observations.</td>
            <td class="reportRowHeading" colspan="1" valign="top">
              <a href="https://geo-ide.noaa.gov/wiki/index.php?title=Platforms">More...</a>
            </td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$instrumentKeywordExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Instrument Keywords (<xsl:value-of select="$instrumentKeywordCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Keywords that describe the instrument used to collect the resource.</td>
            <td class="reportRowHeading" valign="top" rowspan="2">The <a href="http://gcmd.nasa.gov/learn/keyword_list.html">NASA Global Change Master Directory</a> is a good choice for keyword thesaurus. <p>In order to be identified by SpiralTracker, the keyword must have MD_KeywordTypeCode = instrument</p></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='instrument']</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$instrumentKeywordThesaurusExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Instrument Keyword Thesaurus (<xsl:value-of select="$instrumentKeywordThesaurusCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords_vocabulary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of a registered authoritative keyword resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='instrument']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$platformKeywordExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Platform Keywords (<xsl:value-of select="$platformKeywordCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Keywords that describe the platform used to collect the resource.</td>
            <td class="reportRowHeading" valign="top" rowspan="2">The <a href="http://gcmd.nasa.gov/learn/keyword_list.html">NASA Global Change Master Directory</a> is a good choice for keyword thesaurus. <p>In order to be identified by SpiralTracker, the keyword must have MD_KeywordTypeCode = platform</p></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='platform']</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$platformKeywordThesaurusExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Platform Keyword Thesaurus (<xsl:value-of select="$platformKeywordThesaurusCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords_vocabulary)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The name of a registered authoritative keyword resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='platform']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title</td>
          </tr>
        </table>
        <a href="#Identification">Identification</a> | <a href="#Extent">Extent</a> | <a href="#Connection">Connection</a> | <a href="#Distribution">Distribution</a> | <a href="#Description">Description</a> | <a href="#Content">Content</a> | <a href="#Lineage">Lineage</a> | <a href="#Acquisition Information">Acquisition Information</a>
        <a name="ISO Core"/>
        <a name="ISO Core Mandatory"/>
        <h2>ISO Core Score: <xsl:value-of select="$ISOCoreTotal"/>/<xsl:value-of select="$ISOCoreMax"/></h2>
        <h2>Mandatory ISO Core Score: <xsl:value-of select="$ISOMandatoryTotal"/>/<xsl:value-of select="$ISOMandatoryMax"/></h2>
        <p> Note: The ISO Core Score does not count toward the Total Spiral Score.</p>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$titleExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Title</td>
            <td class="reportRowHeading" colspan="1" valign="top">Name by which the dataset or resource is known</td>
            <td class="reportRowHeading" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$abstractExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Abstract</td>
            <td class="reportRowHeading" colspan="1" valign="top">Brief narrative summary of the resource contents.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Abstract narrative should include information on general content and features; dataset application: GIS, CAD, image, database; geographic coverage: county/city name; time period of content: begin and end date or single date; and special data characteristics or limitations. Note: Many applications limit preliminary display to the first 150-200 characters of this field so critical distinguishing characteristics should be listed first.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$creationDateExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Creation Date</td>
            <td class="reportRowHeading" colspan="1" valign="top">Reference date for the cited resource; reference date and event used to describe it.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Whenever possible, include both creation date and revision date. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Dates">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$datasetLanguageCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Language</td>
            <td class="reportRowHeading" colspan="1" valign="top">Languages of the resource using standard ISO three letter codes.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Three letter language code followed by an optional three letter country code: &lt;ISO639-2/T three letter language code&gt;{&lt;blank space&gt;&lt;ISO3166-1 three letter country code&gt;} Language code is given in lowercase. Country code is given in uppercase. e.g. eng fra; CAN This attribute constitutes the default languages of the dataset. see http://www.loc.gov/standards/iso639-2/php/English_list.php for ISO639-2/T language codes; see http://userpage.chemie.fuberlin. de/diverse/doc/ISO_3166.html for ISO3166-1 country codes.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo//gmd:language</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$topicCategoryExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Topic Category (<xsl:value-of select="$topicCategoryCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (keywords)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The main theme(s) of the dataset.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Select topicCategory from MD_TopicCategoryCode. Usually climatologyMeteorologyAtmosphere and/or oceans (keep this capitalization and spacing).</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataContactExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Contact<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">M</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (creator_name, URL, email)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">The responsible party for the metadata content.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The organization directly responsible for metadata maintenance.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:contact</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataDateStampCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Creation Date</td>
            <td class="reportRowHeading" colspan="1" valign="top">Metadata creation date.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Date of metadata creation or the last metadata update. <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Dates">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:dateStamp</td>
          </tr>
        </table>
        <a name="ISO Core Conditional"/>
        <h2>Conditional ISO Core Score: <xsl:value-of select="$ISOConditionalTotal"/>/<xsl:value-of select="$ISOConditionalMax"/></h2>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$resourceExtentExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Spatial Extent</td>
            <td class="reportRowHeading" colspan="1" valign="top">Describes the spatial, horizontal and/or vertical, and the temporal coverage in the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The bounding extent for the resource should be identified with id="boundingExtent": &lt;gmd:EX_Extent id="boundingExtent"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents"> More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude <br/>and<br/> //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude <br/>and<br/> //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude <br/>and<br/> //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude <br/>or<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude <br/>and<br/>              //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude <br/>and<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude <br/>and<br/> //gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataLanguageCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Language</td>
            <td class="reportRowHeading" colspan="1" valign="top">Language of the metadata composed of an ISO639- 2/T three letter language code and an ISO3166-1 three letter country code.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Three letter language code followed by an optional three letter country code: &lt;ISO639-2/T three letter language code&gt;{&lt;;&gt;&lt;blank space&gt;&lt;ISO3166-1 three letter country code&gt;} Language code is given in lowercase. Country code is given in uppercase. e.g. eng fra; CAN This attribute constitutes the default languages of the dataset. see http://www.loc.gov/standards/iso639-2/php/English_list.php for ISO639-2/T language codes; see http://userpage.chemie.fuberlin. de/diverse/doc/ISO_3166.html for ISO3166-1 country codes.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:language</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataCharacterSetCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Character Set</td>
            <td class="reportRowHeading" colspan="1" valign="top">Character coding standard in the metadata.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The character set for the metadata representation is restricted to "utf8", as used for ISO/TS19139:2007 compliant XML encoding.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:characterSet</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$datasetCharacterSetCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Character Set</td>
            <td class="reportRowHeading" colspan="1" valign="top">Character coding standard in the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The default value of the character set for the resource representation is "utf8." The character set should be reported for any resource that uses characters for its representation. Resources such as image and video for instance might not make use of character set. When dataset includes North American aboriginal languages, the character set will not usually be "utf8."</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:characterSet</td>
          </tr>
        </table>
        <a name="ISO Core Optional"/>
        <h2>Optional ISO Core Score: <xsl:value-of select="$ISOOptionalTotal"/>/<xsl:value-of select="$ISOOptionalMax"/></h2>
        <table width="95%" border="1" cellpadding="2" cellspacing="2">
          <tr>
            <th class="reportHeader" valign="top">Score</th>
            <th class="reportHeader" valign="top">Attribute (Count)</th>
            <th class="reportHeader" valign="top">Description</th>
            <th class="reportHeader" valign="top">Recommended Practice</th>
            <th class="reportHeader" valign="top">Path</th>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$temporalExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Temporal Extent</td>
            <td class="reportRowHeading" colspan="1" valign="top">Describes the temporal coverage in the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">A temporal element could be used to describe either the time period covered by the content of the dataset (e.g. during the Jurassic) or the date and time when the data has been collected (e.g. the date on which the geological study was completed). If both are needed, then two temporal extents should be provided. The use of multiple temporal extents should be explained in the attribute description of the extent. The bounding extent for the resource should be identified with id="boundingExtent": &lt;gmd:EX_Extent id="boundingExtent"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$verticalExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Vertical Extent</td>
            <td class="reportRowHeading" colspan="1" valign="top">The elements which give the minimum and maximum of the vertical extent of the dataset.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The bounding extent for the resource should be identified with id="boundingExtent": &lt;gmd:EX_Extent id="boundingExtent"&gt; <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Extents">More...</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$resourceContactExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Contact (<xsl:value-of select="$resourceContactCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a>, <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">UDD (creator_name, URL, email)</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Identification and means to contact people/organizations associated with the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top">The person/organization directly responsible for answering questions about a resource. This could be a person at an archive rather than the originator of the resource (described in the citation).</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$lineageExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Lineage (<xsl:value-of select="$lineageCnt"/>)</td>
            <td class="reportRowHeading" colspan="1" valign="top">Information or lack of information on the events and source data used to construct the resource.</td>
            <td class="reportRowHeading" colspan="1" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage or //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LE_Lineage</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$idExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Identifier</td>
            <td class="reportRowHeading" colspan="1" valign="top">A unique phrase or string which uniquely identifies the metadata file.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Each metadata record shall have a unique identifier, such as a universal unique identifier (UUID), to distinguish it from other resources.</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:fileidentifier</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$distOnlineResourceExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Online Resource (<xsl:value-of select="$distOnlineResourceCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Information about Internet hosted resources: availability; URL; protocol used; resource name; resource description, and resource function.</td>
            <td class="reportRowHeading" colspan="1" valign="top">
              <a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_Online_Resources">More...</a>
            </td>
            <td class="reportRowHeading" colspan="1" valign="top">//gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$spatialRepresentationTypeCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Spatial Representation Type</td>
            <td class="reportRowHeading" colspan="1" valign="top">Object(s) used to represent the geographic information.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Select spatialRepresentationType from <a href="https://geo-ide.noaa.gov/wiki/index.php?title=MD_SpatialRepresentationTypeCode#MD_SpatialRepresentationTypeCode">MD_SpatialRepresentationTypeCode.</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$distributionFormatExist"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Distribution Format (<xsl:value-of select="$distributionFormatCnt"/>)<br/><a href="https://geo-ide.noaa.gov/wiki/index.php?title=ISO_19115_Core_Elements">O</a></td>
            <td class="reportRowHeading" colspan="1" valign="top">Description of distribution format.</td>
            <td class="reportRowHeading" colspan="1" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat/gmd:MD_Forma)</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataStandardNameCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Standard</td>
            <td class="reportRowHeading" colspan="1" valign="top">Name of the metadata standard/profile used.</td>
            <td class="reportRowHeading" colspan="1" valign="top">ISO 19115-2 Geographic Information - Metadata Part 2 Extensions for imagery and gridded data</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:metadataStandardName</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$metadataStandardVersionCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Metadata Version</td>
            <td class="reportRowHeading" colspan="1" valign="top">Version of the metadata standard/profile used.</td>
            <td class="reportRowHeading" colspan="1" valign="top">ISO 19115-2:2009(E)</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:metadataStandardVersion</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$referenceSystemCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Reference System</td>
            <td class="reportRowHeading" colspan="1" valign="top">Description of the spatial and/or temporal reference systems used in the dataset.</td>
            <td class="reportRowHeading" colspan="1" valign="top">Multiple instances of Reference System Information are authorized to describe the coordinate systems being used for coordinate representation (horizontal, vertical and/or temporal).</td>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem</td>
          </tr>
          <tr>
            <xsl:call-template name="showScore">
              <xsl:with-param name="score" select="$spatialResolutionCnt"/>
            </xsl:call-template>
            <td class="reportRowHeading" valign="top">Resource Spatial Resolution</td>
            <td class="reportRowHeading" colspan="1" valign="top">The level of detail of the dataset expressed as equivalent scale or ground distance.</td>
            <td class="reportRowHeading" colspan="1" valign="top"/>
            <td class="reportRowHeading" colspan="1" valign="top">/gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution</td>
          </tr>
        </table>
        <!--  -->
        <hr/> Rubric Version: <xsl:value-of select="$rubricVersion"/><br/>
        <!--  -->
      </body>
    </html>
  </xsl:template>
  <xsl:template name="showColumn">
    <xsl:param name="name"/>
    <xsl:param name="total"/>
    <xsl:param name="max"/>
    <xsl:variable name="column">
      <xsl:choose>
        <xsl:when test="$total=0">0</xsl:when>
        <xsl:when test="$total=$max">4</xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="floor(number(number($total) * 3 div number($max)))+1"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <tr>
      <td class="reportRowHeading" width="20%">
        <a href="#{$name}">
          <xsl:value-of select="$name"/>
        </a>
      </td>
      <xsl:choose>
        <xsl:when test="$column=0">
          <td class="reportRowHeading" align="center" bgcolor="CC00CC"/>
        </xsl:when>
        <xsl:otherwise>
          <td class="reportRowHeading"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
        <xsl:when test="$column=1">
          <td class="reportRowHeading" align="center" bgcolor="CC00CC"/>
        </xsl:when>
        <xsl:otherwise>
          <td class="reportRowHeading"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
        <xsl:when test="$column=2">
          <td class="reportRowHeading" align="center" bgcolor="CC00CC"/>
        </xsl:when>
        <xsl:otherwise>
          <td class="reportRowHeading"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
        <xsl:when test="$column=3">
          <td class="reportRowHeading" align="center" bgcolor="CC00CC"/>
        </xsl:when>
        <xsl:otherwise>
          <td class="reportRowHeading"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:choose>
        <xsl:when test="$column=4">
          <td class="reportRowHeading" align="center" bgcolor="CC00CC"/>
        </xsl:when>
        <xsl:otherwise>
          <td class="reportRowHeading"/>
        </xsl:otherwise>
      </xsl:choose>
    </tr>
  </xsl:template>
  <xsl:template name="showScore">
    <xsl:param name="score"/>
    <xsl:choose>
      <xsl:when test="$score=1">
        <td class="reportRowHeading" align="center" bgcolor="66CC66">
          <xsl:value-of select="$score"/>
        </td>
      </xsl:when>
      <xsl:otherwise>
        <td class="reportRowHeading" align="center" bgcolor="FF0033">
          <xsl:value-of select="$score"/>
        </td>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
