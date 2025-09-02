import loci.formats.FormatException;
import loci.formats.ImageReader;
import loci.formats.meta.IMetadata;
import loci.formats.services.OMEXMLService;
import loci.common.services.ServiceFactory;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

import loci.common.services.DependencyException;
import loci.common.services.ServiceException;


public class ShowFiles {

    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: java ShowFiles <image-file-path>");
            System.out.println();
            System.out.println("- Read image metadata using Bio-Formats");
            System.out.println("- Extract basic image properties");
            System.out.println();
            return;
        }

        String imagePath = args[0];
        ShowFiles example = new ShowFiles();

        try {
            example.readImageInfo(imagePath);
        } catch (Exception e) {
            System.err.println("Error reading image: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Reads and displays basic information about an image file.
     */
    public void readImageInfo(String imagePath)
            throws FormatException, IOException, DependencyException, ServiceException {

        System.out.println("Reading image: " + imagePath);
        System.out.println("=".repeat(50));

        // Create image reader
        ImageReader reader = new ImageReader();

        // Create metadata store that implements MetadataRetrieve
        ServiceFactory factory = new ServiceFactory();
        OMEXMLService service = factory.getInstance(OMEXMLService.class);
        IMetadata metadata = service.createOMEXMLMetadata();

        // Set the metadata store on the reader BEFORE setId()
        reader.setMetadataStore(metadata);

        try {
            // Initialize the reader with the image file
            reader.setId(imagePath);

            // Display basic image information
            System.out.println("Image Information:");
            System.out.println("- Format: " + reader.getFormat());
            System.out.println("- Dimensions: " + reader.getSizeX() + " x " + reader.getSizeY());
            System.out.println("- Series count: " + reader.getSeriesCount());
            System.out.println("- Pixel type: " + reader.getPixelType());
            System.out.println("- Bits per pixel: " + reader.getBitsPerPixel());
            System.out.println("- RGB channel count: " + reader.getRGBChannelCount());
            System.out.println("- Dimension order: " + reader.getDimensionOrder());
            System.out.println("- Little endian: " + reader.isLittleEndian());
            System.out.println("- Interleaved: " + reader.isInterleaved());
            System.out.println("- Indexed: " + reader.isIndexed());

            if (metadata.getPlateCount() > 0) {
                // Show used files per image
                Set<String> commonFiles = new HashSet<>();
                Set<String> tmp = new HashSet<>();
                reader.setSeries(0);
                for (String file : reader.getSeriesUsedFiles(false)) {
                    tmp.add(file);
                }
                reader.setSeries(1);
                for (String file : reader.getSeriesUsedFiles(false)) {
                    if (tmp.contains(file)) {
                        commonFiles.add(file);
                    }
                }
                System.out.println("Used Files:");
                for (int series = 0; series < reader.getSeriesCount(); series++) {
                    reader.setSeries(series);
                    System.out.println("Name: " + metadata.getImageName(series));
                    for (String file : reader.getSeriesUsedFiles(false)) {
                        if (!commonFiles.contains(file)) {
                            System.out.println("  " + file);
                        }
                    }
                }
            }
        } finally {
            reader.close();
        }
    }
}
