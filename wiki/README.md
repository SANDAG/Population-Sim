# Wiki README

This directory contains the source files for the SANDAG PopulationSim GitHub Wiki.

## Wiki Structure

The wiki uses a hybrid approach with overview pages and detailed technical references:

### Core Pages
- **[Home.md](Home.md)** - Landing page with quick links and overview
- **[Getting-Started.md](Getting-Started.md)** - Quick start guide for new users
- **[System-Overview.md](System-Overview.md)** - Architecture and key concepts
- **[FAQ.md](FAQ.md)** - Frequently asked questions

### Reference Pages
- **[Control-Variables.md](Control-Variables.md)** - Complete list of 56 control variables
- **[Output-Files.md](Output-Files.md)** - File formats and specifications

### Additional Pages Needed

You may want to create these additional pages based on the technical documentation:

- **Installation-and-Setup.md** - Detailed installation instructions
- **Running-PopulationSim.md** - Complete execution workflow
- **Data-Preparation.md** - Seed data and control generation details
- **Algorithm-Details.md** - IPF methodology deep dive
- **Validation-and-QA.md** - Quality assurance procedures
- **Troubleshooting.md** - Common issues and solutions
- **Configuration-Reference.md** - Settings and parameters
- **Geographic-Structure.md** - Region, PUMA, MGRA details
- **ABM-Integration.md** - Using outputs in ABM
- **Database-Integration.md** - SQL Server ETL (legacy)
- **Data-Lake-Integration.md** - Modern data export (in development)

## Publishing to GitHub Wiki

### Option 1: Manual Copy-Paste

1. Go to your repository's Wiki tab: `https://github.com/SANDAG/Population-Sim/wiki`
2. Click "New Page" for each .md file
3. Copy the content from each file in this directory
4. Paste into the GitHub Wiki editor
5. Save each page

### Option 2: Git-Based Wiki (Recommended)

GitHub wikis are Git repositories. You can clone and push directly:

```bash
# Clone the wiki repository
git clone https://github.com/SANDAG/Population-Sim.wiki.git

# Copy wiki files
cp wiki/*.md Population-Sim.wiki/

# Commit and push
cd Population-Sim.wiki
git add *.md
git commit -m "Initial wiki structure"
git push origin master
```

### Option 3: Automated Script

```powershell
# PowerShell script to sync wiki files
$wikiRepo = "https://github.com/SANDAG/Population-Sim.wiki.git"
$tempDir = "$env:TEMP\Population-Sim.wiki"

# Clone wiki
git clone $wikiRepo $tempDir

# Copy files
Copy-Item -Path "wiki\*.md" -Destination $tempDir -Force

# Push changes
cd $tempDir
git add *.md
git commit -m "Update wiki pages"
git push origin master

# Cleanup
cd ..
Remove-Item -Recurse -Force $tempDir
```

## Wiki Naming Conventions

GitHub Wiki converts filenames to page titles:
- `Home.md` → "Home" (landing page)
- `Getting-Started.md` → "Getting Started"
- `System-Overview.md` → "System Overview"

Use hyphens for multi-word pages (not spaces or underscores).

## Linking Between Pages

Use relative links without the `.md` extension:

```markdown
See the [Getting Started](Getting-Started) guide.
Check [FAQ](FAQ) for common questions.
```

GitHub Wiki automatically converts these to proper links.

## Images and Diagrams

### Mermaid Diagrams
Already included in the wiki pages using:

```markdown
​```mermaid
flowchart TD
    A[Start] --> B[End]
​```
```

GitHub Wiki renders these automatically.

### Image Files
If you need to add images:

1. Upload to wiki assets: `https://github.com/SANDAG/Population-Sim/wiki/_assets/`
2. Reference in markdown:
```markdown
![Alt text](_assets/image-name.png)
```

## Updating the Wiki

### Workflow
1. Edit files in `wiki/` directory of main repository
2. Commit changes to main repo
3. Sync to GitHub Wiki (using one of the methods above)
4. Keep both in sync

### Best Practices
- ✅ Edit wiki source files in this directory (version controlled)
- ✅ Use mermaid diagrams for visualizations
- ✅ Keep pages focused and concise
- ✅ Cross-link related pages
- ❌ Don't edit directly on GitHub Wiki (changes get lost)
- ❌ Don't duplicate content (link instead)

## Testing Locally

To preview wiki pages locally:

```bash
# Install markdown preview tool
pip install grip

# Preview a page
grip wiki/Home.md
# Opens at http://localhost:6419
```

Or use VS Code with "Markdown Preview Enhanced" extension.

## Maintenance

### Regular Updates Needed
- Update version numbers when releasing new PopulationSim versions
- Update seed data vintage when ACS PUMS changes
- Update forecast years as new years are added
- Update technology stack versions (Python, packages)
- Add new troubleshooting entries as issues arise

### Deprecation
When documenting deprecated features (e.g., SQL Server database):
- Mark clearly with "⚠️ Legacy" or "⚠️ Deprecated"
- Link to replacement (e.g., Data Lake Integration)
- Maintain docs temporarily for users on old versions

## Content Sources

Wiki content is derived from:
- `documentation/SANDAG_PopulationSim_Documentation.md` - Comprehensive technical docs
- `README.md` - Repository overview
- Code comments and docstrings
- Team knowledge and best practices

When updating wiki, check these sources for accuracy.

## Contributing

To improve the wiki:

1. Edit files in `wiki/` directory
2. Submit pull request to main repository
3. After approval, sync to GitHub Wiki
4. Announce significant wiki updates to team

## Support

For questions about the wiki:
- Check existing wiki pages first
- Review comprehensive technical documentation
- Contact SANDAG Modeling team

---

**Ready to publish?** Follow the "Publishing to GitHub Wiki" instructions above.
