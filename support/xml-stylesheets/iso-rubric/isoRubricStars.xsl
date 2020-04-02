<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:gco="http://www.isotc211.org/2005/gco" xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gml="http://www.opengis.net/gml" xmlns:gts="http://www.isotc211.org/2005/gts" xmlns:gmi="http://www.isotc211.org/2005/gmi" xmlns:srv="http://www.isotc211.org/2005/srv" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink">
	<xd:doc xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl" scope="stylesheet">
		<xd:desc>
			<xd:p><xd:b>Created on:</xd:b> Mar 4, 2010</xd:p>
			<xd:p><xd:b>Author:</xd:b> ted.habermann@noaa.gov</xd:p>
			<xd:p/>
		</xd:desc>
	</xd:doc>

	<xsl:output omit-xml-declaration="yes"/>

	<xsl:template match="gmi:MI_Metadata/gmd:MD_Metadata" name="stars">
		<!-- *************** -->
		<!-- calculation variables; must match variables in isoRubricHTML.xsl-->
		<!-- *************** -->
		<xsl:variable name="title" select="//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString"/>
		<!-- ISO Mandatory Core Fields: 7 possible -->
		<xsl:variable name="titleExist">
			<xsl:choose>
				<xsl:when test="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString) = 1">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="titleCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<xsl:variable name="creationDateCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date)"/>
		<xsl:variable name="creationDateExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeListValue='creation']      or //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeListValue='revision']      or //gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeListValue='publication']      )">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="datasetLanguageCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:language/gmd:LanguageCode or gmd:language/gco:CharacterString )"/>
		<xsl:variable name="topicCategoryCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode)"/>
		<xsl:variable name="topicCategoryExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="abstractExist">
			<xsl:choose>
				<xsl:when test="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString) = 1">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="abstractCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString)"/>
		<xsl:variable name="metadataContactExist">
			<xsl:choose>
				<xsl:when test="(//gmi:MI_Metadata/gmd:contact|gmd:MD_Metadata/gmd:contact)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="metadataContactCnt" select="count(gmi:MI_Metadata/gmd:contact|gmd:MD_Metadata/gmd:contact)"/>
		<xsl:variable name="metadataDateStampCnt" select="count(gmi:MI_Metadata/gmd:dateStamp|gmd:MD_Metadata/gmd:dateStamp)"/>
		<xsl:variable name="ISOMandatoryTotal" select="$titleExist + $creationDateExist + $datasetLanguageCnt + $topicCategoryExist + $abstractExist     + $metadataContactCnt + $metadataDateStampCnt"/>
		<xsl:variable name="ISOMandatoryMax">7</xsl:variable>
		<!-- ISO Conditional Core Fields: 4 possible -->
		<xsl:variable name="metadataLanguageCnt" select="count(gmi:MI_Metadata/gmd:language|gmd:MD_Metadata/gmd:language)"/>
		<xsl:variable name="metadataCharacterSetCnt" select="count(gmi:MI_Metadata/gmd:characterSet|gmd:MD_Metadata/gmd:characterSet)"/>
		<xsl:variable name="datasetCharacterSetCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:characterSet)"/>
		<xsl:variable name="datasetExtentExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:geographicElement/gmd:EX_GeographicBoundingBox)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="datasetExtentCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:geographicElement/gmd:EX_GeographicBoundingBox)"/>
		<xsl:variable name="ISOConditionalTotal" select="$metadataLanguageCnt + $metadataCharacterSetCnt + $datasetCharacterSetCnt + $datasetExtentExist"/>
		<xsl:variable name="ISOConditionalMax">4</xsl:variable>
		<!--  -->
		<!-- ISO Optional Core Fields: 12 possible -->
		<xsl:variable name="temporalExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:temporalElement/gmd:EX_TemporalExtent[@id='boundingTemporalExtent']/gmd:extent)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="temporalCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:temporalElement/gmd:EX_TemporalExtent[@id='boundingTemporalExtent']/gmd:extent)"/>
		<xsl:variable name="verticalExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:verticalElement/gmd:EX_VerticalExtent[@id='boundingVerticalExtent']/gmd:minimumValue/gco:Real)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="verticalCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:verticalElement/gmd:EX_VerticalExtent[@id='boundingVerticalExtent']/gmd:minimumValue/gco:Real)"/>
		<xsl:variable name="resourceContactExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="resourceContactCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty)"/>
		<xsl:variable name="lineageExist">
			<xsl:choose>
				<xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="lineageCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage)"/>
		<xsl:variable name="distOnlineResourceExist">
			<xsl:choose>
<!--  To fix the 4 star issue
				<xsl:when test="(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL)">1</xsl:when>
-->
<xsl:when test="(//gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL      | /*/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>

<!-- to fix the 4 star issue
		<xsl:variable name="distOnlineResourceCnt"
			select="count(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL)"/>
-->

<xsl:variable name="distOnlineResourceCnt" select="count(//gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL    | //gmd:distributionInfo//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL    | /*/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL)"/>
  
		<xsl:variable name="onlineResourceURLExist">
			<xsl:choose>
				<xsl:when test="(//gmd:CI_OnlineResource/gmd:linkage/gmd:URL)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="onlineResourceURLCnt" select="count(//gmd:CI_OnlineResource/gmd:linkage/gmd:URL)"/>
		<xsl:variable name="onlineResourceNameExist">
			<xsl:choose>
				<xsl:when test="(//gmd:CI_OnlineResource/gmd:name/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="onlineResourceNameCnt" select="count(//gmd:CI_OnlineResource/gmd:name/gco:CharacterString)"/>
		<xsl:variable name="allOnlineResourceNamesExist">
			<xsl:choose>
				<xsl:when test="($onlineResourceNameCnt = $onlineResourceURLCnt)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="onlineResourceDescExist">
			<xsl:choose>
				<xsl:when test="(//gmd:CI_OnlineResource/gmd:description/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="onlineResourceDescCnt" select="count(//gmd:CI_OnlineResource/gmd:description/gco:CharacterString)"/>
		<xsl:variable name="allOnlineResourceDescExist">
			<xsl:choose>
				<xsl:when test="($onlineResourceDescCnt = $onlineResourceURLCnt)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>

		<xsl:variable name="onlineResourceFunctionCnt" select="count(//gmd:CI_OnlineResource/gmd:description/gco:CharacterString)"/>
		<xsl:variable name="allOnlineResourceFunctionExist">
			<xsl:choose>
			<xsl:when test="$onlineResourceURLCnt and ($onlineResourceFunctionCnt = $onlineResourceURLCnt)">1</xsl:when>
			<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
																	    

		<xsl:variable name="idExist">
			<xsl:choose>
				<xsl:when test="(gmi:MI_Metadata/gmd:fileIdentifier|gmd:MD_Metadata/gmd:fileIdentifier)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="idCnt" select="count(gmi:MI_Metadata/gmd:fileIdentifier|gmd:MD_Metadata/gmd:fileIdentifier)"/>
		<xsl:variable name="spatialRepresentationTypeCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType)"/>
		<xsl:variable name="distributionFormatExist">
			<xsl:choose>
				<xsl:when test="(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat/gmd:MD_Format)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="distributionFormatCnt" select="count(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat/gmd:MD_Format)"/>
		<xsl:variable name="metadataStandardNameCnt" select="count(//gmd:metadataStandardName/gco:CharacterString)"/>
		<xsl:variable name="metadataStandardVersionCnt" select="count(//gmd:metadataStandardVersion/gco:CharacterString)"/>
		<xsl:variable name="referenceSystemCnt" select="count(gmi:MI_Metadata/gmd:referenceSystemInfo|gmd:MD_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem)"/>
		<xsl:variable name="spatialResolutionCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution)"/>
		<xsl:variable name="ISOOptionalTotal" select="$temporalExist + $verticalExist + $resourceContactExist + $lineageExist + $distOnlineResourceExist     + $idExist + $spatialRepresentationTypeCnt  + $distributionFormatExist + $metadataStandardNameCnt + $metadataStandardVersionCnt     + $referenceSystemCnt + $spatialResolutionCnt"/>
		<xsl:variable name="ISOOptionalMax">12</xsl:variable>
		<xsl:variable name="ISOCoreTotal" select="$ISOMandatoryTotal + $ISOOptionalTotal + $ISOConditionalTotal"/>
		<xsl:variable name="ISOCoreMax" select="$ISOMandatoryMax + $ISOOptionalMax + $ISOConditionalMax"/>
		<!--  -->
		<xsl:variable name="datasetExtentDescriptionExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:description/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="datasetExtentDescriptionCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent[@id='boundingExtent']/gmd:description/gco:CharacterString)"/>
		<!-- Keyword Type Fields -->
		<xsl:variable name="themeKeywordExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='theme'])">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="themeKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='theme'])"/>
		<xsl:variable name="themeKeywordThesaurusExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='theme']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="themeKeywordThesaurusCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='theme']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<!--  -->
		<xsl:variable name="dataCenterKeywordExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='dataCenter'])">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="dataCenterKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='dataCenter'])"/>
		<xsl:variable name="dataCenterKeywordThesaurusExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='dataCenter']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="dataCenterKeywordThesaurusCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='dataCenter']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<!--  -->
		<xsl:variable name="projectKeywordExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='project'])">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="projectKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='project'])"/>
		<xsl:variable name="projectKeywordThesaurusExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='project']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="projectKeywordThesaurusCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='project']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<!--  -->
		<xsl:variable name="placeKeywordExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='place'])">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="placeKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='place'])"/>
		<xsl:variable name="placeKeywordThesaurusExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='place']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="placeKeywordThesaurusCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='place']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<!--  -->
		<xsl:variable name="instrumentKeywordExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='instrument'])">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="instrumentKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='instrument'])"/>
		<xsl:variable name="instrumentKeywordThesaurusExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='instrument']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="instrumentKeywordThesaurusCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='instrument']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<!--  -->
		<xsl:variable name="platformKeywordExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='platform'])">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="platformKeywordCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='platform'])"/>
		<xsl:variable name="platformKeywordThesaurusExist">
			<xsl:choose>
				<xsl:when test="(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='platform']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="platformKeywordThesaurusCnt" select="count(//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='platform']/ancestor::node()/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
		<!-- Identification Spiral Scores -->
		<xsl:variable name="citationDateExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<!-- Distribution Spiral Scores -->
		<xsl:variable name="distributorContactExist">
			<xsl:choose>
				<xsl:when test="(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact/gmd:CI_ResponsibleParty)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="distributorContactCnt" select="count(//gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact/gmd:CI_ResponsibleParty)"/>
		<xsl:variable name="graphicOverviewCnt" select="count(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString)"/>
		<xsl:variable name="graphicOverviewExist">
			<xsl:choose>
				<xsl:when test="(//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<!-- Description Scores -->
		<xsl:variable name="purposeExist">
			<xsl:choose>
				<xsl:when test="(//gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:purpose/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="purposeCnt" select="count(//gmi:MI_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:purpose/gco:CharacterString)"/>
		<xsl:variable name="lineageStatementExist">
			<xsl:choose>
				<xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="lineageStatementCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString)"/>
		<!-- Content Information Scores -->
		<xsl:variable name="contentTypeExist">
			<xsl:choose>
				<xsl:when test="(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:contentType/gmd:MD_CoverageContentTypeCode)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="contentTypeCnt" select="count(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:contentType/gmd:MD_CoverageContentTypeCode)"/>
		<xsl:variable name="dimensionNameExist">
			<xsl:choose>
				<xsl:when test="(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:dimension/gmd:MD_Band/gmd:sequenceIdentifier/gco:MemberName/gco:aName/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="dimensionNameCnt" select="count(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:dimension/gmd:MD_Band/gmd:sequenceIdentifier/gco:MemberName/gco:aName/gco:CharacterString)"/>
		<xsl:variable name="dimensionDescriptorExist">
			<xsl:choose>
				<xsl:when test="(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:dimension/gmd:MD_Band/gmd:descriptor/gco:CharacterString)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="dimensionDescriptorCnt" select="count(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:dimension/gmd:MD_Band/gmd:descriptor/gco:CharacterString)"/>
		<xsl:variable name="dimensionUnitsExist">
			<xsl:choose>
				<xsl:when test="(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:dimension/gmd:MD_Band/gmd:units)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="dimensionUnitsCnt" select="count(//gmd:contentInfo/gmi:MI_CoverageDescription/gmd:dimension/gmd:MD_Band/gmd:units)"/>
		<!-- Lineage Scores -->
		<xsl:variable name="sourceExist">
			<xsl:choose>
				<xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="sourceCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source)"/>
		<xsl:variable name="processStepExist">
			<xsl:choose>
				<xsl:when test="(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LI_ProcessStep|      //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LE_ProcessStep)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="processStepCnt" select="count(//gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LI_ProcessStep|    //gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:processStep/gmd:LE_ProcessStep)"/>
		<!-- Acquisition Information Scores -->
		<xsl:variable name="instrumentExist">
			<xsl:choose>
				<xsl:when test="(//gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:instrument/gmi:MI_Instrument)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="instrumentCnt" select="count(//gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:instrument/gmi:MI_Instrument)"/>
		<xsl:variable name="platformExist">
			<xsl:choose>
				<xsl:when test="(//gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform)">1</xsl:when>
				<xsl:otherwise>0</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="platformCnt" select="count(//gmi:MI_Metadata/gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform)"/>
		<!-- Spiral Scores -->
		<xsl:variable name="identificationTotal" select="$idExist + $titleExist  + $abstractExist + $citationDateExist + $topicCategoryExist + $themeKeywordExist + $themeKeywordThesaurusExist + $metadataContactExist + $resourceContactExist"/>
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
		<xsl:variable name="extentTotal" select="$datasetExtentExist + $temporalExist  + $verticalExist + $placeKeywordExist + $placeKeywordThesaurusExist"/>
		<xsl:variable name="extentMax">5</xsl:variable>
	<!--	<xsl:variable name="connectionTotal" select="$onlineResourceURLExist + $allOnlineResourceNamesExist + $allOnlineResourceDescExist"/>
	    -->
	    <!-- Added   allOnlineResourceFuctionExist to get the right connection Total to fix the 4 star issue -->
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

<!-- distOnlineResource<xsl:value-of select="$distOnlineResourceExist"/>
-->

<!--connectionTotal<xsl:value-of select="$connectionTotal"/>  -->

		<!-- *************** -->
		<xsl:call-template name="showstars">
			<xsl:with-param name="name" select="'Total Spiral'"/>
			<xsl:with-param name="total" select="$spiralTotal"/>
			<xsl:with-param name="max" select="$spiralMax"/> 
    
		</xsl:call-template>
	</xsl:template>
	<xsl:template name="showstars">
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
<!--
Column<xsl:value-of select="$column"/>
Total<xsl:value-of select="$total"/>
Max<xsl:value-of select="$max"/>
-->
		<xsl:choose>
			<xsl:when test="$column=0">
				<span class="sprite star_0_0" xmlns="http://www.w3.org/1999/xhtml"></span>
			</xsl:when>
			<xsl:when test="$column=1">
				<span class="sprite star_1_0" xmlns="http://www.w3.org/1999/xhtml"></span>
			</xsl:when>
			<xsl:when test="$column=2">
				<span class="sprite star_2_0" xmlns="http://www.w3.org/1999/xhtml"></span>
			</xsl:when>
			<xsl:when test="$column=3">
				<span class="sprite star_3_0" xmlns="http://www.w3.org/1999/xhtml"></span>
			</xsl:when>
			<xsl:when test="$column=4">
				<span class="sprite star_4_0" xmlns="http://www.w3.org/1999/xhtml"></span>
		        </xsl:when> 
	 		<xsl:otherwise>
				<span class="sprite star_5_0" xmlns="http://www.w3.org/1999/xhtml"></span>
			</xsl:otherwise>
		</xsl:choose>
<!-- Stars<xsl:value-of select="$column"/> -->
	</xsl:template>
</xsl:stylesheet>