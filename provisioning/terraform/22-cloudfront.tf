#
# This file is used to define resources for distribution resources managed through Cloudfront

# ADD Data Catalogue (Integration)
#
# This distribution does not use caching to optimise for development
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource implicitly depends on the 'aws_acm_certificate_validation.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider being previously configured
#
# AWS source: https://aws.amazon.com/cloudfront/
# Terraform source: https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html
#
# Tags are not supported by this resource
resource "aws_cloudfront_distribution" "add-catalogue-integration" {
  enabled = true
  comment = "ADD Data Catalogue (Integration)"

  default_root_object = "index.html"

  # Selects US and EU edge locations only
  #
  # Note: Antarctic ships and stations connect to the internet in London.
  # Source: https://aws.amazon.com/cloudfront/pricing/#price-classes for valid values and included locations
  price_class = "PriceClass_100"

  aliases = [
    "${aws_s3_bucket.add-catalogue-integration.bucket}",
  ]

  # Origin configuration
  #
  # Note: CloudFront to the Origin uses HTTP, End-consumers to CloudFront uses HTTPS
  origin {
    domain_name = "${aws_s3_bucket.add-catalogue-integration.website_endpoint}"
    origin_id   = "S3_${aws_s3_bucket.add-catalogue-integration.bucket}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"

      origin_ssl_protocols = [
        "TLSv1.2",
      ]
    }
  }

  # Behaviours
  default_cache_behavior {
    target_origin_id = "S3_${aws_s3_bucket.add-catalogue-integration.bucket}"

    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 31536000

    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS",
    ]

    cached_methods = [
      "GET",
      "HEAD",
    ]

    forwarded_values {
      query_string = false

      headers = [
        "Origin",
      ]

      cookies {
        forward = "none"
      }
    }
  }

  # Restrictions (not used but must be defined by Terraform)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Enable SSL/TLS for aliases
  #
  # In this configuration a certificate previously uploaded to the Amazon Certificate Manager is used
  viewer_certificate {
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.1_2016"
    acm_certificate_arn      = "${aws_acm_certificate_validation.add-catalogue-integration.certificate_arn}"
  }
}

# ADD Data Catalogue (Production)
#
# This distribution uses caching (1 hour) to optimise for performance
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-production' resource
# This resource implicitly depends on the 'aws_acm_certificate_validation.add-catalogue-production' resource
# This resource relies on the AWS Terraform provider being previously configured
#
# AWS source: https://aws.amazon.com/cloudfront/
# Terraform source: https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html
#
# Tags are not supported by this resource
resource "aws_cloudfront_distribution" "add-catalogue-production" {
  enabled = true
  comment = "ADD Data Catalogue (Production)"

  default_root_object = "index.html"

  # Selects US and EU edge locations only
  #
  # Note: Antarctic ships and stations connect to the internet in London.
  # Source: https://aws.amazon.com/cloudfront/pricing/#price-classes for valid values and included locations
  price_class = "PriceClass_100"

  aliases = [
    "${aws_s3_bucket.add-catalogue-production.bucket}",
  ]

  # Origin configuration
  #
  # Note: CloudFront to the Origin uses HTTP, End-consumers to CloudFront uses HTTPS
  origin {
    domain_name = "${ aws_s3_bucket.add-catalogue-production.website_endpoint }"
    origin_id   = "S3_${aws_s3_bucket.add-catalogue-production.bucket}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"

      origin_ssl_protocols = [
        "TLSv1.2",
      ]
    }
  }

  # Behaviours
  default_cache_behavior {
    target_origin_id = "S3_${aws_s3_bucket.add-catalogue-production.bucket}"

    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 31536000

    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS",
    ]

    cached_methods = [
      "GET",
      "HEAD",
    ]

    forwarded_values {
      query_string = false

      headers = [
        "Origin",
      ]

      cookies {
        forward = "none"
      }
    }
  }

  # Restrictions (not used but must be defined by Terraform)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Enable SSL/TLS for aliases
  #
  # In this configuration a certificate previously uploaded to the Amazon Certificate Manager is used
  viewer_certificate {
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.1_2016"
    acm_certificate_arn      = "${aws_acm_certificate_validation.add-catalogue-production.certificate_arn}"
  }
}
