<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2"
  xmlns:ha="http://www.alerting.net/namespace/index_1.0" version="1.0">

  <xsl:import href="dst_check.xsl"/>
  
  <xsl:output method="html"
   doctype-system="http://www.w3.org/TR/html4/strict.dtd" 
   doctype-public="-//W3C//DTD HTML 4.01//EN" indent="yes" />
  
  
  <!-- Feed header -->
  <xsl:template match="cap:alert">

  <html>
    <head>
     <title>
      <xsl:value-of select="cap:note/text()"/>
     </title>
     <link rel="stylesheet" type="text/css" href="/main.css" />
    </head>
    <style type="text/css">
      body { font-size: 62.5%; }
      body { background: #FFF url(/images/background1.gif); }
      .label { width: 25px; font-weight: bold; vertical-align: text-top; text-align: right;}
      .xsllocation { font-size: 18px; color: white; font-weight: bold; font-family: Verdana, Geneva, Arial, Helvetica, sans-serif; }
      .entry { background-color: #ffffff; width: 100%; margin-top: 5px; border: 1px solid black; }
      .detail,.headline {  font-weight: bold; }
      .light,.area { font-weight: normal; }

      .alert { width: 100%; margin-top: 5px; background-color: #e0e0e0; font-family: Verdana, Geneva, Arial, Helvetica, sans-serif; }
      .banner { height: 30px; vertical-align: top; }
      .info { background-color: #ffffff; width: 100%; margin-top: 5px; border: 1px solid black; line-height: 110%  }
      .tiny { text-align: left; }
      .tinyLabel { font-weight: bold; vertical-align: text-top; text-align: right; }
      .detail { background-color: #e0e0e0; margin-right: 20px; }
      .headline { font-size: 1.2em; }
      .description { font-size: 1.0em; }

    </style>
    <body>

     <!-- start main content -->
     <div style="margin: 0; padding: 0; width: 525px; position: absolute; top: 120px; left: 125px;">
      <table width="525" cellspacing="2" cellpadding="0" border="0">
        <tr valign="top">
          <td>&#160;&#160;&#160;&#160;&#160;&#160;&#160;</td>
          <xsl:variable name="lcletters">abcdefghijklmnopqrstuvwxyz</xsl:variable>
          <xsl:variable name="ucletters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>
          <xsl:variable name="st">
           <xsl:value-of select="substring(substring-after(cap:identifier/text(),'NOAA-NWS-ALERTS-'),1,2)"/>
          </xsl:variable>
          <xsl:variable name="lcst">
           <xsl:value-of select="translate(substring(substring-after(cap:identifier/text(),'NOAA-NWS-ALERTS-'),1,2),$ucletters,$lcletters)"/>
          </xsl:variable>

          <xsl:variable name="forecastoffice">
            <xsl:value-of select="cap:info/cap:senderName/text()"/>
          </xsl:variable>

          <td width="100%"><p><a name="contents" id="contents"></a><a href="/">Home</a> &gt; <a href="./">Alerts</a> &gt; 
           <a border="0">
            <xsl:attribute name="href">
             <xsl:copy-of select="$lcst"/>.php?x=1
            </xsl:attribute>
            <xsl:choose>
             <xsl:when test="contains(cap:note/text(),'(')">
              <xsl:value-of select="substring-before(substring-after(cap:note/text(),'('),')')"/>
             </xsl:when>
             <xsl:otherwise>
              <xsl:copy-of select="$st"/>
             </xsl:otherwise>
            </xsl:choose>
           </a>
           &gt; <xsl:value-of select="cap:info/cap:event/text()"/> Issued by <xsl:copy-of select="$forecastoffice"/></p>
           <table class="alert">
            <tr>
             <td class="label">Message:</td>
             <td>
              <xsl:value-of select="cap:identifier/text()"/><span class="tiny"> from </span><xsl:value-of select="cap:sender/text()"/>
             </td>
            </tr>
            <tr>
             <td class="label">Sent:</td>
             <td>
              <xsl:value-of select="substring(normalize-space(cap:sent/text()), 12, 5)"/>
              <xsl:call-template name="timeZoneName">
               <xsl:with-param name="offset" select="substring(normalize-space(cap:sent/text()), 20, 6)"/>
               <xsl:with-param name="year" select="substring(normalize-space(cap:sent/text()), 1, 4)"/>
               <xsl:with-param name="month" select="substring(normalize-space(cap:sent/text()), 6, 2)"/>
               <xsl:with-param name="day" select="substring(normalize-space(cap:sent/text()), 9, 2)"/>
               <xsl:with-param name="st" select="$lcst"/>
              </xsl:call-template>
              <span class="tiny"> on </span>
              <xsl:value-of select="substring(normalize-space(cap:sent/text()), 1, 10)"/>
             </td>
            </tr>
            <tr>
             <td class="label">Effective:</td>
             <td>
              <xsl:value-of select="substring(normalize-space(cap:info/cap:effective/text()), 12, 5)"/>
              <xsl:call-template name="timeZoneName">
               <xsl:with-param name="offset" select="substring(normalize-space(cap:info/cap:effective/text()), 20, 6)"/>
               <xsl:with-param name="year" select="substring(normalize-space(cap:info/cap:effective/text()), 1, 4)"/>
               <xsl:with-param name="month" select="substring(normalize-space(cap:info/cap:effective/text()), 6, 2)"/>
               <xsl:with-param name="day" select="substring(normalize-space(cap:info/cap:effective/text()), 9, 2)"/>
               <xsl:with-param name="st" select="$lcst"/>
              </xsl:call-template>
              <span class="tiny"> on </span>
              <xsl:value-of select="substring(normalize-space(cap:info/cap:effective/text()), 1, 10)"/>
             </td>
            </tr>
            <tr>
             <td class="label">Expires:</td>
             <td>
              <xsl:value-of select="substring(normalize-space(cap:info/cap:expires/text()), 12, 5)"/>
              <xsl:call-template name="timeZoneName">
               <xsl:with-param name="offset" select="substring(normalize-space(cap:info/cap:expires/text()), 20, 6)"/>
               <xsl:with-param name="year" select="substring(normalize-space(cap:info/cap:expires/text()), 1, 4)"/>
               <xsl:with-param name="month" select="substring(normalize-space(cap:info/cap:expires/text()), 6, 2)"/>
               <xsl:with-param name="day" select="substring(normalize-space(cap:info/cap:expires/text()), 9, 2)"/>
               <xsl:with-param name="st" select="$lcst"/>
              </xsl:call-template>
              <span class="tiny"> on </span>
              <xsl:value-of select="substring(normalize-space(cap:info/cap:expires/text()), 1, 10)"/>
             </td>
            </tr>
            <tr>
             <td colspan="2">
              <table class="entry">
               <tr>
                <td class="label">Event:</td>
                <td class="headline"><xsl:value-of select="cap:info/cap:event/text()"/></td>
               </tr>
               <tr>
                <td class="label">Alert:</td>
                <td class="description">
                 <xsl:variable name="descrip">
                  <xsl:call-template name="globalReplace">
                   <xsl:with-param name="outputString" select="substring(cap:info/cap:description/text(),1)"/>
                   <xsl:with-param name="target" select="'&#xa;&#42;'"/>
                   <xsl:with-param name="replacement" select="'&#xa;&#xa;&#42;'"/>
                  </xsl:call-template> 
                 </xsl:variable>
                 <xsl:variable name="descrip2">
                  <xsl:call-template name="globalReplace">
                   <xsl:with-param name="outputString" select="$descrip"/>
                   <xsl:with-param name="target" select="'&#xa;&#46;'"/>
                   <xsl:with-param name="replacement" select="'&#xa;&#xa;&#46;'"/>
                  </xsl:call-template> 
                 </xsl:variable>
                 <xsl:variable name="descrip3">
                  <xsl:call-template name="globalReplace">
                   <xsl:with-param name="outputString" select="$descrip2"/>
                   <xsl:with-param name="target" select="'&#46;&#46;&#46;&#xa;THE'"/>
                   <xsl:with-param name="replacement" select="'&#46;&#46;&#46;&#xa;&#xa;THE'"/>
                  </xsl:call-template> 
                 </xsl:variable>
                 <xsl:variable name="descrip4">
                  <xsl:call-template name="globalReplace">
                   <xsl:with-param name="outputString" select="$descrip3"/>
                   <xsl:with-param name="target" select="'&#46;&#46;&#46;&#xa;A'"/>
                   <xsl:with-param name="replacement" select="'&#46;&#46;&#46;&#xa;&#xa;A'"/>
                  </xsl:call-template> 
                 </xsl:variable>
                 <!-- force a space before newline to facilitate url links -->
                 <xsl:variable name="descrip5">
                  <xsl:call-template name="globalReplace">
                   <xsl:with-param name="outputString" select="$descrip4"/>
                   <xsl:with-param name="target" select="'&#xa;'"/>
                   <xsl:with-param name="replacement" select="' &#xa;'"/>
                  </xsl:call-template>
                 </xsl:variable>
                 <!-- make links hot -->
                 <xsl:variable name="descrip6">
                  <xsl:call-template name="hotlink">
                   <xsl:with-param name="text" select="$descrip5"/>
                   <xsl:with-param name="searchterm1" select="'HTTP'"/>
                  </xsl:call-template>
                 </xsl:variable>
                 <pre class="description">
                  <xsl:copy-of select="$descrip6"/>
                 </pre>
                </td>
               </tr>
               <tr>
                <td class="label">Instructions:</td>
                <td class="description"><xsl:value-of select="cap:info/cap:instruction/text()"/></td>
               </tr>
               <tr>
                <td class="label">Target Area:</td>
                <td>
                 <table class="detail">
                  <tr>
                   <td colspan="2">
                    <xsl:variable name="areas1">
                     <xsl:call-template name="globalReplace">
                      <xsl:with-param name="outputString" select="cap:info/cap:area/cap:areaDesc/text()"/>
                      <xsl:with-param name="target" select="'/'"/>
                      <xsl:with-param name="replacement" select="'&#xa;'"/>
                     </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="areas">
                     <xsl:call-template name="globalReplace">
                      <xsl:with-param name="outputString" select="$areas1"/>
                      <xsl:with-param name="target" select="';'"/>
                      <xsl:with-param name="replacement" select="'&#xa;'"/>
                     </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="firstchar" select="substring($areas,1,1)"/>
                    <xsl:choose>
                     <xsl:when test = "$firstchar = '&#xa;'"> <!-- first character is a carriage return -->
                      <xsl:call-template name="br-replace">
                       <xsl:with-param name="text" select="substring($areas,2)"/>
                      </xsl:call-template>
                     </xsl:when>
                     <xsl:otherwise>
                      <xsl:call-template name="br-replace">
                       <xsl:with-param name="text" select="$areas"/>
                      </xsl:call-template>
                     </xsl:otherwise>
                    </xsl:choose>
                   </td>
                  </tr>
                 </table>
                </td>
               </tr>
              </table>
             </td>
            </tr>
            <tr>
             <td class="label">Forecast Office:</td>
             <td><xsl:value-of select="cap:info/cap:senderName/text()"/></td>
            </tr>
           </table>
          </td>
        </tr>
      </table> 
      <!-- start of footer -->
      <xsl:variable name="footer" select="document('/includes/footer.php')"/> 
      <xsl:copy-of select="$footer"/>
      <!-- end of footer -->
     </div> 
     <!-- end of main content -->
    </body>
  </html>
  </xsl:template>

  <!-- Time Zone function -->
  <xsl:template name="timeZoneName">
   <xsl:param name="offset"/>
   <xsl:param name="year"/>
   <xsl:param name="month"/>
   <xsl:param name="day"/>
   <xsl:param name="st"/>

   <!-- determine if its DST or not, based on run time -->
   <xsl:variable name="dst_start">
    <xsl:call-template name="day-light-savings-start">
     <xsl:with-param name="year" select="$year"/>
    </xsl:call-template>
   </xsl:variable>

   <xsl:variable name="dst_end">
    <xsl:call-template name="day-light-savings-end">
     <xsl:with-param name="year" select="$year"/>
    </xsl:call-template>
   </xsl:variable>

   <xsl:variable name="tod_jul">
    <xsl:call-template name="date-to-absolute-day">
     <xsl:with-param name="year" select="$year"/>
     <xsl:with-param name="month" select="$month"/>
     <xsl:with-param name="day" select="$day"/>
    </xsl:call-template>
   </xsl:variable>

   <xsl:variable name="dst_flag">
    <xsl:choose>
     <xsl:when test="$dst_start &lt;= $tod_jul and $dst_end &gt;= $tod_jul">dst</xsl:when>
     <xsl:otherwise>nodst</xsl:otherwise>
    </xsl:choose>
   </xsl:variable>

   <xsl:if test="$offset = '+10:00'"> <xsl:text> ChST</xsl:text> </xsl:if>
   <xsl:if test="$offset = '-11:00'"> <xsl:text> SST</xsl:text> </xsl:if>
   <xsl:if test="$offset = '-10:00'"> <xsl:text> HST</xsl:text> </xsl:if>
   <xsl:if test="$offset = '-00:00'"> <xsl:text> GMT</xsl:text> </xsl:if>
   <xsl:if test="$offset = '+00:00'"> <xsl:text> GMT</xsl:text> </xsl:if>

   <xsl:choose>
    <xsl:when test="$dst_flag = 'nodst'">
     <xsl:if test="$offset = '-09:00'"> <xsl:text> AKST</xsl:text> </xsl:if>
     <xsl:if test="$offset = '-08:00'"> <xsl:text> PST</xsl:text> </xsl:if>
     <xsl:if test="$offset = '-07:00'"> <xsl:text> MST</xsl:text> </xsl:if>
     <xsl:if test="$offset = '-06:00'"> <xsl:text> CST</xsl:text> </xsl:if>
     <xsl:if test="$offset = '-05:00'"> <xsl:text> EST</xsl:text> </xsl:if>
     <xsl:if test="$offset = '-04:00'"> <xsl:text> AST</xsl:text> </xsl:if>
    </xsl:when>
    <xsl:otherwise>
     <xsl:choose>
      <xsl:when test="$st = 'az'">
       <xsl:if test="$offset = '-08:00'"> <xsl:text> PST</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-07:00'"> <xsl:text> MST</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-06:00'"> <xsl:text> CST</xsl:text> </xsl:if>
      </xsl:when>
      <xsl:otherwise>
       <xsl:if test="$offset = '-08:00'"> <xsl:text> AKDT</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-07:00'"> <xsl:text> PDT</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-06:00'"> <xsl:text> MDT</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-05:00'"> <xsl:text> CDT</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-04:00'"> <xsl:text> EDT</xsl:text> </xsl:if>
       <xsl:if test="$offset = '-03:00'"> <xsl:text> ADT</xsl:text> </xsl:if>
      </xsl:otherwise>
     </xsl:choose>
    </xsl:otherwise>
   </xsl:choose>

  </xsl:template>

  <!-- Replace function -->
  <xsl:template name="globalReplace">
   <xsl:param name="outputString"/>
   <xsl:param name="target"/>
   <xsl:param name="replacement"/>
   <xsl:choose>
     <xsl:when test="contains($outputString,$target)">

       <xsl:value-of select=
         "concat(substring-before($outputString,$target),$replacement)"/>
       <xsl:call-template name="globalReplace">
         <xsl:with-param name="outputString" select="substring-after($outputString,$target)"/>
         <xsl:with-param name="target" select="$target"/>
         <xsl:with-param name="replacement" select="$replacement"/>
       </xsl:call-template>
     </xsl:when>
     <xsl:otherwise>
       <xsl:value-of select="$outputString"/>
     </xsl:otherwise>
   </xsl:choose>
  </xsl:template>

  <!-- Replace new lines with html <br> tags -->
  <xsl:template name="br-replace">
    <xsl:param name="text"/>
    <xsl:variable name="cr" select="'&#xa;'"/>
    <xsl:choose>
      <!-- If the value of the $text parameter contains carriage ret -->
      <xsl:when test="contains($text,$cr)">
        <!-- Return the substring of $text before the carriage return -->
        <xsl:value-of select="substring-before($text,$cr)"/>
        <!-- And construct a <br/> element -->
        <br/>
        <!--
         | Then invoke this same br-replace template again, passing the
         | substring *after* the carriage return as the new "$text" to
         | consider for replacement
         +-->
        <xsl:call-template name="br-replace">
          <xsl:with-param name="text" select="substring-after($text,$cr)"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise>
   </xsl:choose>
  </xsl:template>

  <!-- If it looks like a link, make it hot -->
  <xsl:template name="hotlink">
   <xsl:param name="text"/>
   <xsl:param name="searchterm1"/>

   <xsl:variable name="lcletters">abcdefghijklmnopqrstuvwxyz</xsl:variable>
   <xsl:variable name="ucletters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>

   <xsl:choose>
    <xsl:when test="contains($text,$searchterm1)">

     <!-- grab data before the searchterm -->
      <xsl:value-of select="substring-before($text,$searchterm1)"/>
      <a border="0">
      <xsl:attribute name="href"> 
     <!-- determine actual link by taking data from the searchterm to 
          either the space or the newline - whichever is first  -->
      <xsl:value-of select="translate(concat($searchterm1,substring-before(substring-after($text,$searchterm1),' ')),$ucletters,$lcletters)"/>
     </xsl:attribute>
     <xsl:value-of select="translate(concat($searchterm1,substring-before(substring-after($text,$searchterm1),' ')),$ucletters,$lcletters)"/> </a>

     <!-- data after the link - check for more links -->
     <xsl:call-template name="hotlink">
      <xsl:with-param name="text" select="substring-after(substring-after($text,$searchterm1),' ')"/>
      <xsl:with-param name="searchterm1" select="$searchterm1"/>
     </xsl:call-template> 
    </xsl:when>
    <xsl:otherwise>
     <xsl:value-of select="$text"/>
    </xsl:otherwise> 
   </xsl:choose> 
  </xsl:template>

  <!-- Ignore anything else -->
  <xsl:template match="*"></xsl:template>

</xsl:stylesheet>
