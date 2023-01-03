# YO12-downloader
YOOOOOOOOOOOO! *pon*
The purpose of this code is to create a local archive of the images and metadata found on ukiyo-e.org.<br><br>

# Data Model
For a concrete example of the data model consider a print like this one: https://ukiyo-e.org/image/mfa/sc130578<br>
This print would result in a filepath of: `Katsushika Hokusai/mfa_sc130578.jpg`<br><br>
The date, artist, and description are embedded in the exif metadata description tag as essentially a stable diffusion style prompt:<br>
`Katsushika Hokusai, Surugadai in Edo (Tôto sundai), from the series Thirty-six Views of Mount Fuji (Fugaku sanjûrokkei), 1830-31`

# Limitations
* Complete metadata is not available for all images.
* Some of the metadata has not been fully translated and parts remain in Japanese.
* There are semi-duplicated data with some popular prints such as the great wave having many different scans of both the same and different print runs.
* A handful of images on ukiyo-e.org contain errors and won't be downloaded
* A number of the images are low quality, low resolution, and are non-aligned photographs that include picture frames.
